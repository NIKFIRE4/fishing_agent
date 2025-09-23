using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TgParse.Helpers
{
    public class FFMpeg
    {
        Process ffmpeg;
        public void exec(Stream input, Stream output, string parametri)
        {
            ffmpeg = new Process();

            ffmpeg.StartInfo.Arguments = " -i " + input + (parametri != null ? " " + parametri : "") + " " + output;
            ffmpeg.StartInfo.FileName = Directory.GetCurrentDirectory();
            ffmpeg.StartInfo.UseShellExecute = false;
            ffmpeg.StartInfo.RedirectStandardOutput = true;
            ffmpeg.StartInfo.RedirectStandardError = true;
            ffmpeg.StartInfo.CreateNoWindow = true;

            ffmpeg.Start();
            ffmpeg.WaitForExit();
            ffmpeg.Close();
        }


        public void GetThumbnail(Stream video, Stream jpg, string velicina)
        {
            if (velicina == null) velicina = "640x480";
            exec(video, jpg, "-s " + velicina);
        }
    }
}
