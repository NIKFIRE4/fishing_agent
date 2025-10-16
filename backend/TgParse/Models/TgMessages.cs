using System.ComponentModel.DataAnnotations;

namespace TgParse.Models
{
    public class TgMessages
    {
        [Key]
        public int IdTgMessage { get; set; }
        public int MessageId { get; set; }
        public string? MessageText { get; set; }
        public string? SourceUrl { get; set; }
        public int? PlaceId { get; set; }
        public int? IdRegion { get; set; }
        public bool IsProcessed { get; set; }
        public Places? Place { get; set; }
        public List<TgPhotos>? Photos { get; set; } = new List<TgPhotos>();
        public Regions? Region {  get; set; }
    }
}
