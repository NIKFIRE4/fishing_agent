using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.Hosting;
using DBShared;
using TgParse.Services;
using StackExchange.Redis;
using TgParse.Data;
using FFMpegCore;

namespace TgParse
{
    class Program
    {
        static void ApplyMigrations(IServiceProvider services)
        {
            using var scope = services.CreateScope();
            var context = scope.ServiceProvider.GetRequiredService<ApplicationContext>();
            try
            {
                Console.WriteLine("Applying database migrations...");
                context.Database.Migrate();
                Console.WriteLine("Migrations applied successfully!");
                
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error applying migrations: {ex.Message}");
                Environment.Exit(1);
            }
        }

        static void Main(string[] args)
        {
            DotNetEnv.Env.Load();

            var builder = WebApplication.CreateBuilder(args);

            // Регистрация зависимостей
            builder.Services.AddDbContext<ApplicationContext>();
            builder.Services.AddSingleton<IConnectionMultiplexer>(sp =>
                ConnectionMultiplexer.Connect(
                    $"{Environment.GetEnvironmentVariable("REDIS_HOST")}:{Environment.GetEnvironmentVariable("REDIS_PORT")}," +
                    $"password={Environment.GetEnvironmentVariable("REDIS_PASSWORD")}"));
            builder.Services.AddSingleton<CacheService>();
            builder.Services.AddScoped<MessageComparor>();
            builder.Services.AddControllers();
            builder.Services.AddEndpointsApiExplorer();
            builder.Services.AddSwaggerGen();

            var app = builder.Build();

            // Применяем миграции при старте
            ApplyMigrations(app.Services);

            // Настройка FFmpeg
            GlobalFFOptions.Configure(options =>
            {
                options.BinaryFolder = Path.Combine(AppContext.BaseDirectory, "FFmpeg");
                options.TemporaryFilesFolder = Path.GetTempPath();
            });

            // Вызов кэширования при старте
            //using (var scope = app.Services.CreateScope())
            //{
            //    var db = scope.ServiceProvider.GetRequiredService<ApplicationContext>();
            //    var cache = scope.ServiceProvider.GetRequiredService<CacheService>();
            //    cache.CacheAllPlacesAsync(db).Wait();
            //}

            // Swagger и маршруты
            app.UseSwagger();
            app.UseSwaggerUI();
            app.UseHttpsRedirection();
            app.MapControllers();

            app.Run();
        }
    }
}
