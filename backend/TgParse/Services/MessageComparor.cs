using Microsoft.EntityFrameworkCore;
using System.Text.Json;
using TgParse.Data;
using DBShared.Models;
using DBShared;

namespace TgParse.Services
{
    public class MessageComparor
    {
        private readonly ApplicationContext _context;

        public MessageComparor(ApplicationContext context)
        {
            _context = context;
        }

        public async Task ProcessUnprocessedMessagesAsync()
        {
            // Выбираем необработанные сообщения
            var unprocessedMessages = await _context.TgMessages
                .Where(m => !m.IsProcessed)
                .Take(100)
                .ToListAsync();

            if (!unprocessedMessages.Any())
            {
                Console.WriteLine("Нет необработанных сообщений.");
                return;
            }

            foreach (var message in unprocessedMessages)
            {
                try
                {
                    var jsonResult = await PlaceComparor.DataConverter(message.MessageText ?? string.Empty,
                        message.SourceUrl ?? string.Empty);

                    if (jsonResult == null)
                    {
                        Console.WriteLine($"Ошибка обработки сообщения {message.MessageId}: Нет ответа от ML.");
                        continue;
                    }

                    // Десериализуем JSON в PlaceResponse
                    var placeResponse = JsonSerializer.Deserialize<PlaceResponse>(jsonResult);
                    if (placeResponse == null || string.IsNullOrEmpty(placeResponse.NameLocation))
                    {
                        Console.WriteLine($"Ошибка обработки сообщения {message.MessageId}: Некорректный ответ ML.");
                        continue;
                    }

                    // Начинаем транзакцию
                    using var transaction = await _context.Database.BeginTransactionAsync();

                    // Ищем место, если new_place = false
                    Places? place = null;
                    if (!placeResponse.NewPlace)
                    {
                        place = await _context.Places
                            .Include(p => p.PlaceVectors)
                            .FirstOrDefaultAsync(p => p.PlaceName == placeResponse.NameLocation);
                    }

                    if (place == null)
                    {
                        // Создаём новое место
                        place = new Places
                        {
                            PlaceName = placeResponse.NameLocation,
                            PlaceType = placeResponse.TypeOfRelax,
                            Latitude = placeResponse.PlaceCoordinates?.Count == 2 ? placeResponse.PlaceCoordinates[0] : null,
                            Longitude = placeResponse.PlaceCoordinates?.Count == 2 ? placeResponse.PlaceCoordinates[1] : null,
                            PlaceDescription = placeResponse.Description,
                            UserPreferences = placeResponse.UserPreferences,
                            PlaceVectors = new PlaceVectors
                            {
                                NameEmbedding = placeResponse.NameEmbedding,
                                PreferencesEmbedding = placeResponse.PreferencesEmbedding
                            }
                        };
                        _context.Places.Add(place);
                    }
                    else
                    {
                        // Перезаписываем существующее место
                        place.PlaceName = placeResponse.NameLocation;
                        place.PlaceType = placeResponse.TypeOfRelax;
                        place.Latitude = placeResponse.PlaceCoordinates?.Count == 2 ? placeResponse.PlaceCoordinates[0] : null;
                        place.Longitude = placeResponse.PlaceCoordinates?.Count == 2 ? placeResponse.PlaceCoordinates[1] : null;
                        place.PlaceDescription = placeResponse.Description;
                        place.UserPreferences = placeResponse.UserPreferences;

                        // Обновляем или создаём эмбеддинги
                        if (place.PlaceVectors == null)
                        {
                            place.PlaceVectors = new PlaceVectors
                            {
                                NameEmbedding = placeResponse.NameEmbedding,
                                PreferencesEmbedding = placeResponse.PreferencesEmbedding
                            };
                        }
                        else
                        {
                            place.PlaceVectors.NameEmbedding = placeResponse.NameEmbedding;
                            place.PlaceVectors.PreferencesEmbedding = placeResponse.PreferencesEmbedding;
                        }

                        // Удаляем старые связи с рыбами и водоёмами
                        var oldFishLinks = await _context.FishingPlaceFish
                            .Where(fpf => fpf.IdFishingPlace == place.IdPlace)
                            .ToListAsync();
                        var oldWaterLinks = await _context.FishingPlaceWater
                            .Where(fpw => fpw.IdFishingPlace == place.IdPlace)
                            .ToListAsync();
                        _context.FishingPlaceFish.RemoveRange(oldFishLinks);
                        _context.FishingPlaceWater.RemoveRange(oldWaterLinks);
                    }

                    await _context.SaveChangesAsync(); // Сохраняем место для получения IdPlace

                    // Обрабатываем FishType
                    var caughtFishes = placeResponse.CaughtFishes ?? new List<string>();
                    foreach (var fishName in caughtFishes)
                    {
                        if (string.IsNullOrEmpty(fishName)) continue;
                        var fishType = await _context.FishType.FirstOrDefaultAsync(ft => ft.FishName == fishName);
                        if (fishType == null)
                        {
                            fishType = new FishType { FishName = fishName };
                            _context.FishType.Add(fishType);
                            await _context.SaveChangesAsync();
                        }
                        _context.FishingPlaceFish.Add(new FishingPlaceFish
                        {
                            IdFishingPlace = place.IdPlace,
                            IdFishType = fishType.IdFishType
                        });
                    }

                    // Обрабатываем WaterType
                    var waterSpaces = placeResponse.WaterSpace ?? new List<string>();
                    foreach (var waterName in waterSpaces)
                    {
                        if (string.IsNullOrEmpty(waterName)) continue;
                        var waterType = await _context.WaterType.FirstOrDefaultAsync(wt => wt.WaterName == waterName);
                        if (waterType == null)
                        {
                            waterType = new WaterType { WaterName = waterName };
                            _context.WaterType.Add(waterType);
                            await _context.SaveChangesAsync();
                        }
                        _context.FishingPlaceWater.Add(new FishingPlaceWater
                        {
                            IdFishingPlace = place.IdPlace,
                            IdWaterType = waterType.IdWaterType
                        });
                    }

                    // Обновляем сообщение
                    message.PlaceId = place.IdPlace;
                    message.IsProcessed = true;
                    _context.TgMessages.Update(message);

                    // Сохраняем все изменения
                    await _context.SaveChangesAsync();
                    await transaction.CommitAsync();
                    Console.WriteLine($"Обработано сообщение {message.MessageId}, место: {place.PlaceName} ({(placeResponse.NewPlace ? "создано" : "обновлено")})");
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Ошибка обработки сообщения {message.MessageId}: {ex.Message}");
                    // Можно добавить retry или пометить сообщение как проблемное
                }
            }
        }
    }
}

