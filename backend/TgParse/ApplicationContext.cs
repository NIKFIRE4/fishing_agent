using Microsoft.EntityFrameworkCore;
using TgParse.Models;

namespace TgParse.Data
{    
    public class ApplicationContext : DbContext
    {
        public DbSet<TgMessages> TgMessages { get; set; }
        public DbSet<TgPhotos> TgPhotos { get; set; }

        protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        {
            var connectionString = Environment.GetEnvironmentVariable("DB_CONNECTION_STRING")
            ?? "${DB_CONNECTION_STRING}"
            ;

            optionsBuilder.UseNpgsql(connectionString);
        }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<TgMessages>()
                .HasMany(m => m.Photos)
                .WithOne(p => p.Message)
                .HasForeignKey(p => p.MessageId)
                .OnDelete(DeleteBehavior.Cascade);

            modelBuilder.Entity<TgMessages>()
                .HasIndex(m => m.MessageId)
                .IsUnique();

            //modelBuilder.Entity<FishingPlaces>()
            //    .HasIndex(m => m.PlaceId)
            //    .IsUnique();
        }
    }
}
