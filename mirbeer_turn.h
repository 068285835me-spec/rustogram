/*
 * MirBeer TURN credentials provider.
 * Fetches TURN server list from Auth API and caches for 24 hours.
 */
#pragma once

#include <vector>
#include <string>
#include <tgcalls/Instance.h>

namespace MirBeer {

constexpr auto kApiUrl = "https://api.turn.mirbeer.xyz:8443/turn-credentials";
constexpr auto kApiKey = "69d286fbab3d6bea0066e06d01dafdad50803ee669a0bddc2cf879c807877942";
constexpr auto kCacheTtlSeconds = 86400; // 24 часа

// Запрашивает серверы с API асинхронно и кэширует
void FetchTurnServers();

// Возвращает закэшированный список серверов (пустой если ещё не получили)
std::vector<tgcalls::RtcServer> GetCachedTurnServers();

// Инициализация — вызывать при старте приложения
void Initialize();

} // namespace MirBeer
