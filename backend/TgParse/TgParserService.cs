using Docker.DotNet.Models;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using ServiceStack;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
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
                    
                    int a = Console.ReadLine().ToInt();
                    if (a == 1)
                    {
                        _logger.LogInformation("Starting parsing at {Time}", DateTime.UtcNow);
                        await TelegramParser.RunApplication();

                        _logger.LogInformation($"Parsing completed ");
                    }
                    else if (a == 2)
                    {
                        var response = await PlaceComparor.DataConverter(
                            " Подарок всем подписчикам - интерактивная кapта, где коллективным трудом собрано более 400 различных мест: подъезды к воде, спуски для лодок, парковки у берега, + во многих местах рядом можно поставить палатку. Карта по водоёмам: Ладога, ФЗ, Вуокса, Спб, Волхов, Луга, Свирь, озёра севера и юга ЛО. Если где-то спускают лодку, значит рядом есть и рыба  – ЗАБРАТЬ КАРТУ   Интерактивная карта мест для рыбалки с берега в межсезонье и зимой по открытой воде  ЗАБРАТЬ КАРТУ    Платные услуги для рыбаков: 1) Карты рыбных мест от 4000 руб. (на карася, щуку, леща, окуня) 2) Аренда лодок и моторов на Вуоксе от 2500 руб. 3) Новейшие карты глубин от 1500 руб. 4) Рыбалка с гидом на Вуоксе от 13000 руб/день.  Более подробно всё это можно посмотреть на САЙТЕ или в сообществе РЫБАГИД   Автор канала: @rybalka_spb_andrey   Все ПРАВИЛА любительской рыбалки всегда есть на САЙТЕ Северо-Западного территориального управления Федерального агентства по рыболовству.   Телефоны «горячей линии» рыбоохраны: 88005506964; и 8(921)9313216  Съездили на рыбалку? Поделитесь своим результатом!  Отправляйте свои материалы к нам в бота и мы скоро опубликуем   ️Для отправки переходите по кнопке ниже ️",
                            "рыбалка");                       
                        
                        _logger.LogInformation($"Result: {response} ");

                    }
                    else continue;




                        await Task.Delay(TimeSpan.FromHours(1), stoppingToken);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error during parsing");

                    await Task.Delay(TimeSpan.FromMinutes(5), stoppingToken);
                }
            }

            _logger.LogInformation("TgParserService stopped");
        }
    }
}
