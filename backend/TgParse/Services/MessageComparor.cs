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
            var unprocessedMessages = await _context.TgMessages
                .Where(m => !m.IsProcessed)
                .Take(100)
                .ToListAsync();

            if (!unprocessedMessages.Any())
            {
                Console.WriteLine("Нет необработанных сообщений для обработки.");
                return;
            }

            foreach (var message in unprocessedMessages)
            {
                try
                {
                    // Проверяем, что сообщение содержит текст и URL
                    if (string.IsNullOrEmpty(message.MessageText) || string.IsNullOrEmpty(message.SourceUrl))
                    {
                        Console.WriteLine($"Пропуск сообщения {message.MessageId}: текст или URL пусты.");
                        message.IsProcessed = true;
                        _context.TgMessages.Update(message);
                        await _context.SaveChangesAsync();
                        continue;
                    }

                    // Отправляем сообщение в ML-сервис
                    var jsonResult = await PlaceComparor.DataConverter(message.MessageText, message.SourceUrl);
                    if (jsonResult == null)
                    {
                        Console.WriteLine($"Ошибка обработки сообщения {message.MessageId}: ML-сервис не вернул ответ.");
                        continue;
                    }

                    // Десериализуем ответ ML-сервиса
                    PlaceResponse? placeResponse;
                    try
                    {
                        placeResponse = JsonSerializer.Deserialize<PlaceResponse>(jsonResult);
                        if (placeResponse == null || string.IsNullOrEmpty(placeResponse.NameLocation))
                        {
                            Console.WriteLine($"Ошибка обработки сообщения {message.MessageId}: некорректный ответ ML (пустое имя места).");
                            continue;
                        }
                    }
                    catch (JsonException ex)
                    {
                        Console.WriteLine($"Ошибка десериализации ответа ML для сообщения {message.MessageId}: {ex.Message}");
                        continue;
                    }

                    // Начинаем транзакцию
                    using var transaction = await _context.Database.BeginTransactionAsync();

                    try
                    {
                        string? normalizedPlaceName = placeResponse.NameLocation?.Trim().ToLowerInvariant();
                        // Проверяем существование места
                        Places? place = null;
                        if (!placeResponse.NewPlace)
                        {
                            place = await _context.Places
                                .Include(p => p.PlaceVectors)
                                .FirstOrDefaultAsync(p => p.PlaceName != null && p.PlaceName.Trim().ToLowerInvariant() == normalizedPlaceName);
                        }

                        // Если место не найдено, создаем новое
                        if (place == null)
                        {
                            place = new Places
                            {
                                PlaceName = placeResponse.NameLocation,
                                PlaceType = placeResponse.TypeOfRelax,
                                Latitude = placeResponse.PlaceCoordinates?.Count == 2 ? placeResponse.PlaceCoordinates[0] : null,
                                Longitude = placeResponse.PlaceCoordinates?.Count == 2 ? placeResponse.PlaceCoordinates[1] : null,
                                PlaceDescription = placeResponse.Description,
                                UserPreferences = placeResponse.UserPreferences ?? new List<string>(),
                                PlaceVectors = new PlaceVectors
                                {
                                    NameEmbedding = placeResponse.NameEmbedding?.Count > 0 ? placeResponse.NameEmbedding : new List<float>(),
                                    PreferencesEmbedding = placeResponse.PreferencesEmbedding?.Count > 0 ? placeResponse.PreferencesEmbedding : new List<float>()
                                }
                            };
                            _context.Places.Add(place);
                        }
                        else
                        {
                            // Обновляем существующее место
                            place.PlaceName = placeResponse.NameLocation;
                            place.PlaceType = placeResponse.TypeOfRelax;
                            place.Latitude = placeResponse.PlaceCoordinates?.Count == 2 ? placeResponse.PlaceCoordinates[0] : null;
                            place.Longitude = placeResponse.PlaceCoordinates?.Count == 2 ? placeResponse.PlaceCoordinates[1] : null;
                            place.PlaceDescription = placeResponse.Description;
                            place.UserPreferences = placeResponse.UserPreferences ?? new List<string>();

                            // Обновляем или создаем эмбеддинги
                            if (place.PlaceVectors == null)
                            {
                                place.PlaceVectors = new PlaceVectors
                                {
                                    IdPlace = place.IdPlace,
                                    NameEmbedding = placeResponse.NameEmbedding?.Count > 0 ? placeResponse.NameEmbedding : new List<float>(),
                                    PreferencesEmbedding = placeResponse.PreferencesEmbedding?.Count > 0 ? placeResponse.PreferencesEmbedding : new List<float>()
                                };
                                _context.PlaceVectors.Add(place.PlaceVectors);
                            }
                            else
                            {
                                place.PlaceVectors.NameEmbedding = placeResponse.NameEmbedding?.Count > 0 ? placeResponse.NameEmbedding : new List<float>();
                                place.PlaceVectors.PreferencesEmbedding = placeResponse.PreferencesEmbedding?.Count > 0 ? placeResponse.PreferencesEmbedding : new List<float>();
                            }

                            // Удаляем старые связи с рыбами и водоемами
                            var oldFishLinks = await _context.FishingPlaceFish
                                .Where(fpf => fpf.IdFishingPlace == place.IdPlace)
                                .ToListAsync();
                            var oldWaterLinks = await _context.FishingPlaceWater
                                .Where(fpw => fpw.IdFishingPlace == place.IdPlace)
                                .ToListAsync();
                            _context.FishingPlaceFish.RemoveRange(oldFishLinks);
                            _context.FishingPlaceWater.RemoveRange(oldWaterLinks);
                        }

                        // Сохраняем место для получения IdPlace
                        await _context.SaveChangesAsync();

                        // Обрабатываем FishType
                        var caughtFishes = placeResponse.CaughtFishes ?? new List<string>();
                        foreach (var fishName in caughtFishes)
                        {
                            if (string.IsNullOrEmpty(fishName)) continue;

                            var fishType = await _context.FishType
                                .FirstOrDefaultAsync(ft => ft.FishName == fishName);

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

                            var waterType = await _context.WaterType
                                .FirstOrDefaultAsync(wt => wt.WaterName == waterName);

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

                        Console.WriteLine($"!!!!!!NEW_______PLACE:{placeResponse.NewPlace}, Обработано сообщение {message.MessageId}, место: {place.PlaceName} ({(placeResponse.NewPlace ? "создано" : "обновлено")})");
                    }
                    catch (DbUpdateException ex)
                    {
                        // Логируем детальную информацию об ошибке
                        Console.WriteLine($"Ошибка сохранения данных для сообщения {message.MessageId}: {ex.Message}");
                        Console.WriteLine($"Внутренняя ошибка: {ex.InnerException?.Message ?? "Нет внутренней ошибки"}");
                        await transaction.RollbackAsync();
                        continue;
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"Общая ошибка обработки сообщения {message.MessageId}: {ex.Message}");
                        await transaction.RollbackAsync();
                        continue;
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Критическая ошибка обработки сообщения {message.MessageId}: {ex.Message}");
                    continue;
                }
            }
        }
    }
}