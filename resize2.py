import math
import os
from turtle import width
from unittest import result
from PIL import Image, ImageDraw
import numpy as np
import xml.etree.ElementTree as ET

from pandas import wide_to_long

def CropImage(filename_jpg, box):
    #   读取图像并转换成RGB图像
    image = Image.open(filename_jpg)
    image = image.convert('RGB')

    # 找出最小边界
    width, height = image.size
    max_x, max_y = 0, 0
    min_x, min_y = width, height
    
    if width / 16 < height / 9:
        prop = width // 16
    else:
        prop = height // 9


    new_w = 16 * prop
    new_h = 9 * prop

    for boxx in box:
        if int(boxx[0]) < min_x:
            min_x = int(boxx[0])
        if int(boxx[1]) < min_y:
            min_y = int(boxx[1])
        if int(boxx[2]) > max_x:
            max_x = int(boxx[2])
        if int(boxx[3]) > max_y:
            max_y = int(boxx[3])

    # 判断剪裁是否包含边框
    diff = max_y - min_y
    y1 = int(min_y + diff /2 - new_h / 2)
    y2 = y1 + new_h
    if y2 > height:
        y2 = height
        y1 = height - new_h
    elif y1 < 0:
        y1 = 0
        y2 = new_h

    diff = max_x - min_x
    x1 = int(min_x + diff /2 - new_w / 2)
    x2 = x1 + new_w
    if (x2 > width):
        x2 = width
        x1 = width - new_w
    elif x1 < 0:
        x1 = 0
        x2 = new_w

    left = x1
    up = y1

    size = (x1, y1, x2, y2)
    new_image = image.crop(size)

    box_resize = []
    for boxx in box:
        boxx[0] = str(int(boxx[0]) - left)
        boxx[1] = str(int(boxx[1]) - up)
        boxx[2] = str(int(boxx[2]) - left)
        boxx[3] = str(int(boxx[3]) - up)
        if (int(boxx[0]) < 0):
            boxx[0] = str(0)
        if (int(boxx[1]) < 0):
            boxx[1] = str(0)
        if (int(boxx[2]) > new_w):
            boxx[2] = str(new_w)
        if (int(boxx[3]) > new_h):
            boxx[3] = str(new_h)
        box_resize.append(boxx)
    return new_image, box_resize

def read_xml(xml_name):
    etree = ET.parse(xml_name)
    root = etree.getroot()
    box = []
    data = dict()
    for obj in root.iter('object'):
        xmin,ymin,xmax,ymax = (x.text for x in obj.find('bndbox'))
        box.append([xmin,ymin,xmax,ymax])
        data[obj.find('name').text]
    return box

def write_xml(xml_name,save_name, box, resize_w, resize_h):
    etree = ET.parse(xml_name)
    root = etree.getroot()

    # 修改图片的宽度、高度
    for obj in root.iter('size'):
        obj.find('width').text = str(resize_w)
        obj.find('height').text = str(resize_h)

    # 修改box的值
    for obj, bo in zip(root.iter('object'), box):
        for index, x in enumerate(obj.find('bndbox')):
            x.text = bo[index]
    etree.write(save_name)

# def start(sourceDir, targetDir, resize_w, resize_h):
def start(sourceDir, targetDir):
    for root, dir1, filenames in os.walk(sourceDir):
        for filename in filenames:
            file = os.path.splitext(filename)[0]
            if os.path.splitext(filename)[1] == '.jpg':
                print('正在进行crop:' + filename)
                filename_jpg = os.path.join(root, filename)
                xml_name = os.path.join(root, file + '.xml')
                box = read_xml(xml_name)

                image_data, box_data = CropImage(filename_jpg, box)
                resize_w, resize_h = image_data.size
                image_data.save(os.path.join(targetDir, filename))

                for j in range(len(box_data)):
                    thickness = 3
                    left, top, right, bottom = box_data[j][0:4]
                    draw = ImageDraw.Draw(image_data)
                    for i in range(thickness):
                        draw.rectangle([int(left) + i, int(top) + i, int(right) - i, int(bottom) - i], outline=(255, 0, 0))
                # 修改xml文件（将修改后的 box 写入到xml文件中）
                save_xml = os.path.join(targetDir, file + '.xml')
                write_xml(xml_name, save_xml, box_data, resize_w, resize_h)
                # 查看box绘制在图片上的效果
                path = './part2_draw_img'
                image_data.save(os.path.join(path, filename))


if __name__ == "__main__":

    # 源文件夹
    sourceDir = "./check_2020.08.24_roadscene_part2/0/"
    # 结果保存文件夹
    targetDir = "./check_2020.08.24_roadscene_part2_res/"

    start(sourceDir, targetDir)
    print('完成！')





