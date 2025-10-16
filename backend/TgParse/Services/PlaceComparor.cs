using System.Text;
using System.Text.Json;
using TgParse.Models;

namespace TgParse.Services
{
    public class PlaceComparor
    {
        public static async Task<JsonDocument?> DataConverter(string message)
        {
            var jsonObject = new { message };
            string json = JsonSerializer.Serialize(jsonObject);

            using HttpClient client = new HttpClient();
            client.BaseAddress = new Uri("http://ml_service:8001/");
            HttpContent content = new StringContent(json, Encoding.UTF8, "application/json");

            Console.WriteLine($"Отправка запроса: {message}");
            HttpResponseMessage response = await client.PostAsync("compare_fishing_places", content);

            if (response.IsSuccessStatusCode)
            {
                string responseBody = await response.Content.ReadAsStringAsync();                
                JsonDocument doc = JsonDocument.Parse(responseBody);
                return doc;
            }
            else
            {
                Console.WriteLine($"Ошибка: {response.StatusCode}");
                return null;
            }
        }
    }
}