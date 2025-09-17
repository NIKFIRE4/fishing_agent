using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using TgParse.Data;
using TgParse.Models;
using TgParse.Services;

namespace TgParse.Data
{
    public class TgMessageSaver
    {
        public static async Task SaveMessageToDb(int messageId, string messageText, Dictionary<string, byte[]> imageData, string channelName)
        {
            Console.WriteLine($"КОЛИЧЕСТОВ ФОТОК ДЛЯ ДБ:: {imageData.Count}");

            using (ApplicationContext db = new())
            {
                var message = new TgMessages
                {
                    MessageText = messageText,
                    MessageId = messageId,
                    СhannelUrl = channelName,
                };
                bool exists = db.TgMessages.Any(m => m.MessageId == message.MessageId);
                if (exists)
                {
                    Console.WriteLine($"Сообщение {message.MessageId} уже в базе");
                }
                else
                {
                    foreach (var imageDB in imageData)
                    {
                        message.Photos?.Add(new TgPhotos { PhotoUrl = imageDB.Key });
                        var uploader = new MinioUploader();
                        await uploader.UploadImage(imageDB.Value, imageDB.Key, "image/jpeg");
                    }
                    db.TgMessages.AddRange(message);
                    db.SaveChanges();
                    Console.WriteLine($"Сообщение {message.MessageId} занесено в базу");
                }
            }
        }
    }
}
