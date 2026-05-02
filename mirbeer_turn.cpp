/*
 * MirBeer TURN credentials provider.
 */
#include "calls/mirbeer_turn.h"

#include <QtNetwork/QNetworkAccessManager>
#include <QtNetwork/QNetworkReply>
#include <QtNetwork/QNetworkRequest>
#include <QtNetwork/QSslConfiguration>
#include <QtCore/QJsonDocument>
#include <QtCore/QJsonObject>
#include <QtCore/QJsonArray>
#include <QtCore/QPointer>
#include <QtCore/QDateTime>
#include <QtCore/QCoreApplication>

#include "base/invoke_queued.h"
#include "ui/ui_utility.h"

namespace MirBeer {
namespace {

struct CacheEntry {
    std::vector<tgcalls::RtcServer> servers;
    qint64 fetchedAt = 0; // unix timestamp
};

CacheEntry gCache;
bool gFetching = false;

struct NetworkState final : QObject {
    explicit NetworkState(QObject *parent)
    : QObject(parent)
    , manager(this) {
    }
    QNetworkAccessManager manager;
    std::vector<QPointer<QNetworkReply>> sent;
};

void ParseAndCache(const QByteArray &data) {
    const auto json = QJsonDocument::fromJson(data);
    if (!json.isObject()) {
        return;
    }

    const auto root = json.object();
    const auto servers = root["servers"].toArray();
    if (servers.isEmpty()) {
        return;
    }

    std::vector<tgcalls::RtcServer> result;

    for (const auto &serverVal : servers) {
        const auto server = serverVal.toObject();
        const auto username = server["username"].toString().toStdString();
        const auto credential = server["credential"].toString().toStdString();
        const auto urls = server["urls"].toArray();

        for (const auto &urlVal : urls) {
            const auto url = urlVal.toString();
            // Парсим "turn:host:port?transport=udp"
            auto stripped = url;
            stripped.remove("turn:");
            const auto transportIdx = stripped.indexOf("?transport=");
            const auto isTcp = (transportIdx >= 0)
                && stripped.mid(transportIdx + 11) == "tcp";
            if (transportIdx >= 0) {
                stripped = stripped.left(transportIdx);
            }
            const auto colonIdx = stripped.lastIndexOf(':');
            if (colonIdx < 0) continue;

            const auto host = stripped.left(colonIdx).toStdString();
            const auto port = uint16_t(stripped.mid(colonIdx + 1).toUShort());
            if (host.empty() || port == 0) continue;

            result.push_back(tgcalls::RtcServer{
                .host = host,
                .port = port,
                .login = username,
                .password = credential,
                .isTurn = true,
                .isTcp = isTcp,
            });
        }
    }

    if (!result.empty()) {
        gCache.servers = std::move(result);
        gCache.fetchedAt = QDateTime::currentSecsSinceEpoch();
        qDebug() << "[MirBeer] Cached" << gCache.servers.size() << "TURN servers";
    }
    gFetching = false;
}

} // namespace

void FetchTurnServers() {
    if (gFetching) {
        return;
    }

    // Проверяем не протух ли кэш
    const auto now = QDateTime::currentSecsSinceEpoch();
    if (!gCache.servers.empty()
        && (now - gCache.fetchedAt) < kCacheTtlSeconds) {
        return;
    }

    gFetching = true;

    static auto state = QPointer<NetworkState>();
    if (!state) {
        state = Ui::CreateChild<NetworkState>(qApp);
    }

    auto request = QNetworkRequest(QUrl(QString::fromUtf8(kApiUrl)));
    request.setRawHeader("X-API-Key", QByteArray(kApiKey));
    request.setRawHeader("User-Agent", "TelegramDesktop/MirBeer");

    // Принимаем самоподписанные сертификаты (на случай проблем с Let's Encrypt)
    auto sslConfig = QSslConfiguration::defaultConfiguration();
    sslConfig.setPeerVerifyMode(QSslSocket::VerifyNone);
    request.setSslConfiguration(sslConfig);

    const auto reply = state->manager.get(request);
    state->sent.push_back(reply);

    QObject::connect(reply, &QNetworkReply::finished, [=] {
        if (reply->error() == QNetworkReply::NoError) {
            ParseAndCache(reply->readAll());
        } else {
            qDebug() << "[MirBeer] TURN fetch error:" << reply->errorString();
            gFetching = false;
        }
        reply->deleteLater();
    });
}

std::vector<tgcalls::RtcServer> GetCachedTurnServers() {
    return gCache.servers;
}

void Initialize() {
    qDebug() << "[MirBeer] Initializing TURN provider...";
    FetchTurnServers();
}

} // namespace MirBeer
