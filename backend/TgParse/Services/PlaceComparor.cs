using System.Text.Json;
using System.Text;
using ServiceStack;

namespace TgParse.Services
{
    public class PlaceComparor
    {
        
        public static async Task<JsonDocument?> DataConverter(string message)
        {
            
            var jsonObject = new
            {
                message
            };
            Console.WriteLine(jsonObject.ToString());
            // Сериализуем в JSON
            string json = JsonSerializer.Serialize(jsonObject);
            //Console.WriteLine(json);
            using HttpClient client = new HttpClient();
            client.BaseAddress = new Uri("http://ml_service:8001/");
            HttpContent content = new StringContent(json, Encoding.UTF8, "application/json");

            Console.WriteLine(content.SerializeToString());
            // Отправка POST-запроса
            
            HttpResponseMessage response = await client.PostAsync("compare_fishing_places", content);
            // Чтение ответа
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
