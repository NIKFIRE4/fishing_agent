using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations.Schema;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace DBShared.Models
{
    
    public class SelectedSpot
    {
        [Key]
        public int id { get; set; } 

        [Required]
        public int user_id { get; set; } 

        [Required]
        [StringLength(255)]
        public string spot_name { get; set; } = null!; 

        [StringLength(100)]
        public string? spot_coordinates { get; set; } 

        [Required]
        public DateTime fishing_date { get; set; } 

        public string? user_query { get; set; } 

        [StringLength(100)]
        public string? user_coordinates { get; set; } 

        public DateTime selected_at { get; set; } = DateTime.UtcNow;
        [ForeignKey("user_id")]
        public UserBot user { get; set; } = null!;
    }
    
}
