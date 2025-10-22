using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace DBShared.Models
{
    public class User
    {
        [Key]
        public int id { get; set; }

        [Required]
        public long tg_id { get; set; }

        [StringLength(64)]
        public string? username { get; set; }

        [StringLength(64)]
        public string? first_name { get; set; }

        [StringLength(64)]
        public string? last_name { get; set; }

        public DateTime created_at { get; set; } = DateTime.UtcNow;

        public List<SelectedSpot> selected_spots { get; set; } = new List<SelectedSpot>();

    }
}
