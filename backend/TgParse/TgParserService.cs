using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using TgParse.Services;

namespace TgParse
{
    public class TgParserService : BackgroundService
    {
        private readonly ILogger<TgParserService> _logger;

        public TgParserService(ILogger<TgParserService> logger)
        {
            _logger = logger;
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            _logger.LogInformation("TgParserService started");

            while (!stoppingToken.IsCancellationRequested)
            {
                try
                {
                    _logger.LogInformation("Starting parsing at {Time}", DateTime.UtcNow);

                    // Вызов парсинга
                    await PlaceComparor.DataConverter(
                        "21.06.25🚩 Река Фонтанка Три судачка, окунь и два схода примерно за час, а дальше начался ливень.🧭 Координаты локации: 59.937886, 30.342723 #малыереки #судак #окунь #рыбалкаисточник (https://vk.com/wall-78578788_72603)");

                    _logger.LogInformation("Parsing completed at {Time}", DateTime.UtcNow);

                    // Задержка перед следующим запуском (например, 1 час)
                    await Task.Delay(TimeSpan.FromHours(1), stoppingToken);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error during parsing");
                    // Задержка перед повторной попыткой, чтобы не зациклиться
                    await Task.Delay(TimeSpan.FromMinutes(5), stoppingToken);
                }
            }

            _logger.LogInformation("TgParserService stopped");
        }
    }
}
