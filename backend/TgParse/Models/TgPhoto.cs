using System.ComponentModel.DataAnnotations;

namespace TgParse.Models
{
    public class TgPhotos
    {
        [Key]
        public int IdTgPhotos { get; set; }
        public string? PhotoUrl { get; set; }
        public int IdTgMessage { get; set; }
        public TgMessages? Messages { get; set; }
    }
}
