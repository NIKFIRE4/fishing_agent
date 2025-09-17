using System.Text;
using System.Text.Json;

namespace TgParse.Services
{
    public static class PersonDetector
    {
        public static async Task<bool> DetectPersonAsync(byte[] byteImage)
        {
            string base64Image = Convert.ToBase64String(byteImage);
            var jsonObject = new
            {
                image = base64Image
            };
            // Сериализуем в JSON
            string json = JsonSerializer.Serialize(jsonObject);
            using HttpClient client = new HttpClient();
            client.BaseAddress = new Uri("http://ml_service:8001/");

            // Сериализация данных в JSON

            HttpContent content = new StringContent(json, Encoding.UTF8, "application/json");

            // Отправка POST-запроса
            HttpResponseMessage response = await client.PostAsync("detect-person", content);

            // Чтение ответа
            if (response.IsSuccessStatusCode)
            {
                string responseBody = await response.Content.ReadAsStringAsync();

                JsonDocument doc = JsonDocument.Parse(responseBody);
                return doc.RootElement.GetProperty("person_detected").GetBoolean();

            }
            else
            {
                Console.WriteLine($"Ошибка: {response.StatusCode}");
                return false;
            }
        }
    }
}
