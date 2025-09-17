using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
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

            await TelegramParser.RunApplication();
        }
    } 
}