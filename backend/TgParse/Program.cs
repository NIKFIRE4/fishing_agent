using FFMpegCore;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using System;
using TgParse.Data;
using TgParse.Services;


namespace TgParse
{
    class Program
    {
        private static void ConfigureServices(IServiceCollection services)
        {
            services.AddDbContext<ApplicationContext>();
        }

        private static void ApplyMigrations(ApplicationContext context)
        {
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

        static async Task Main(string[] args)
        {
            var serviceCollection = new ServiceCollection();
            ConfigureServices(serviceCollection);
            var serviceProvider = serviceCollection.BuildServiceProvider();

            using (var scope = serviceProvider.CreateScope())
            {
                var context = scope.ServiceProvider.GetRequiredService<ApplicationContext>();
                ApplyMigrations(context);
            }
            using ApplicationContext db = new();



            GlobalFFOptions.Configure(options =>
            {
                options.BinaryFolder = Path.Combine(AppContext.BaseDirectory, "FFmpeg");
                options.TemporaryFilesFolder = Path.GetTempPath();
            });


            Console.WriteLine("FFmpeg dir: " + Path.Combine(AppContext.BaseDirectory, "FFmpeg"));
            Console.WriteLine("ffmpeg exists: " + File.Exists(Path.Combine(AppContext.BaseDirectory, "FFmpeg", "ffmpeg.exe")));
            Console.WriteLine("ffprobe exists: " + File.Exists(Path.Combine(AppContext.BaseDirectory, "FFmpeg", "ffprobe.exe")));
            Console.WriteLine("System ffmpeg exists: " + File.Exists("/usr/bin/ffmpeg"));
            Console.WriteLine("System ffprobe exists: " + File.Exists("/usr/bin/ffprobe"));


            await TelegramParser.RunApplication();           
        }
    } 
}