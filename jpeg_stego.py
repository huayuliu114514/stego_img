def insert_com_segment(jpeg_path, output_path, comment_text):
    # 读取 JPEG 字节
    with open(jpeg_path, "rb") as f:
        data = f.read()

    if not (data[0] == 0xFF and data[1] == 0xD8):
        raise ValueError("输入文件不是 JPEG")

    # 将中文等内容直接 UTF-8 编码
    comment_bytes = comment_text.encode("utf-8")

    # COM 段结构：FF FE + 长度 + 数据
    length = len(comment_bytes) + 2
    com_segment = b"\xFF\xFE" + length.to_bytes(2, "big") + comment_bytes

    # 插入到 FFD8 后面
    new_jpeg = data[:2] + com_segment + data[2:]

    with open(output_path, "wb") as f:
        f.write(new_jpeg)

    print("写入完成：", output_path)


if __name__ == "__main__":
    input_jpeg = "lycoris.jpg"
    output_jpeg = "lycoris_stego.jpg"
    secret_text = "helloWorld  "  

    insert_com_segment(input_jpeg, output_jpeg, secret_text)
