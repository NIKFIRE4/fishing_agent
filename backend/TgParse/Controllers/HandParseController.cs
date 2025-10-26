using Microsoft.AspNetCore.Mvc;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using TgParse.Data;
using TgParse.Services;

namespace TgParse.Controllers
{
    internal class HandParseController: ControllerBase
    {
        private readonly MinioUploader _minioUploader;

        public HandParseController(MinioUploader minioUploader)
        {
            _minioUploader = minioUploader;
        }

        public class MessageInputModel
        {
            public string MessageText { get; set; } = string.Empty;
            public List<string> PhotoUrls { get; set; } = new List<string>();
        }

        [HttpPost]
        public async Task<IActionResult> AddMessage([FromBody] MessageInputModel input)
        {
            // Валидация входных данных
            if (string.IsNullOrWhiteSpace(input.MessageText))
            {
                return BadRequest("Текст сообщения не может быть пустым.");
            }

            if (input.PhotoUrls == null || !input.PhotoUrls.Any())
            {
                return BadRequest("Список URL-ов фотографий не может быть пустым.");
            }

            try
            {
                // Словарь для хранения данных изображений
                var imageData = new Dictionary<string, byte[]>();

                // Генерация messageId (на основе текущего времени в тиках)
                int messageId = (int)(DateTime.UtcNow.Ticks % int.MaxValue);

                // Скачивание изображений по URL
                using var httpClient = new HttpClient();
                foreach (var photoUrl in input.PhotoUrls)
                {
                    // Проверка валидности URL
                    if (!Uri.TryCreate(photoUrl, UriKind.Absolute, out var uri))
                    {
                        return BadRequest($"Невалидный URL изображения: {photoUrl}");
                    }

                    // Скачивание изображения
                    var response = await httpClient.GetAsync(photoUrl);
                    if (!response.IsSuccessStatusCode)
                    {
                        return BadRequest($"Не удалось скачать изображение по URL: {photoUrl}");
                    }

                    var imageBytes = await response.Content.ReadAsByteArrayAsync();
                    var contentType = response.Content.Headers.ContentType?.MediaType ?? "image/jpeg";

                    // Формирование имени файла в формате tg{messageId}_{uniqueId}{extension}
                    string uniqueId = Guid.NewGuid().ToString("N");
                    string extension = contentType switch
                    {
                        "image/jpeg" => ".jpg",
                        "image/png" => ".png",
                        "image/gif" => ".gif",
                        _ => ".bin"
                    };
                    string objectName = $"tg{messageId}_{uniqueId}{extension}";

                    

                    // Добавление в словарь
                    imageData[objectName] = imageBytes;
                }

                // Сохранение в базу через TgMessageSaver
                await TgMessageSaver.SaveMessageToDb(messageId, input.MessageText, imageData, "manual_input");

                return Ok(new { Message = $"Сообщение с ID {messageId} успешно сохранено." });
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Ошибка: {ex.Message}");
                return StatusCode(500, "Произошла ошибка при сохранении сообщения.");
            }
        }
    }
}

