private void WriteImageInfoToFile(string filePath,double opacity,int stretch)
   {
       //读取文件数据
       var buffer = System.IO.File.ReadAllBytes(filePath);

       //判断是否是JPG文件
       if (buffer[0] == 0xFF && buffer[1] == 0xD8)
       {
           //将原始数据扩容6个字节
           var newBuffer = new byte[buffer.Length + 6];

           //拷贝JPG文件开始标记 FF D8
           Array.Copy(buffer, 0, newBuffer, 0, 2);

           //设置数据
           //注释标记
           newBuffer[2] = 0xFF;
           newBuffer[3] = 0xFE;
           //大小 0x02
           newBuffer[4] = 0;
           newBuffer[5] = 0x02;
           //数据
           newBuffer[6] = (byte)nOpacity;
           newBuffer[7] = (byte)stretch;

           //将原图片剩下的数据拷贝到新buffer中
           Array.Copy(buffer, 2, newBuffer, 7, buffer.Length - 2);

           //写入文件
           System.IO.File.WriteAllBytes(filePath, newBuffer);
       }
   }