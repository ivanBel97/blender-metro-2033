from texture_tool import DDSUtils


texture_path = input("Введите путь к текстуре: ")
dds_path = DDSUtils.convert_texture(texture_path)

print(f"Всё сохранилось по пути в {dds_path}")
