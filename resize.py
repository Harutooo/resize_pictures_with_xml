import math
import os
import sys
from turtle import width
from unittest import result
from PIL import Image, ImageDraw
import numpy as np
import xml.etree.ElementTree as ET
from pandas import wide_to_long

'''
为了生成可重复key的字典， 对象可以重复
'''
class p(object):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name
    def __str__(self):
        return self.name

#获取最小以及最大边界值
def FindMinOrd(box):
    min_x, min_y, max_x, max_y = sys.maxsize, sys.maxsize, 0, 0
    for boxx in box:
        if int(boxx[0]) < min_x:
            min_x = int(boxx[0])
        if int(boxx[1]) < min_y:
            min_y = int(boxx[1])
        if int(boxx[2]) > max_x:
            max_x = int(boxx[2])
        if int(boxx[3]) > max_y:
            max_y = int(boxx[3])
    return min_x, min_y, max_x, max_y

def FinalMin(box_dict, mid, isx):
    ll, lr = {"vehicle": 0, "sign" : 0, 'crossing' : 0, 'light' : 0}, {"vehicle": 0, "sign" : 0, 'crossing' : 0, 'light' : 0}
    if isx == True:
        for n, ord in box_dict.items():
            s = str(n).split('_')[0]
            if int(ord[0]) < mid:
                # [str(str(name).split('_')[0])]
                ll[s] = ll[s] + 1  
            elif int(ord[2]) > mid:
                lr[s] = ll[s] + 1 
        min = True if ll["sign"] > lr["sign"] else False 
    else:
        for n, ord in box_dict.items():
            s = str(n).split('_')[0]
            if int(ord[1]) < mid:
                ll[s] = ll[s] + 1 
            elif int(ord[3]) > mid:
                lr[s] = ll[s] + 1 
        min = True if ll["sign"] > lr["sign"] else False

    return min

def CropImage(filename_jpg, box, box_dict):
    #   读取图像并转换成RGB图像
    image = Image.open(filename_jpg)
    image = image.convert('RGB')

    # 找出最小边界
    min_x, min_y, max_x, max_y = FindMinOrd(box)

    width, height = image.size
    if width / 16 < height / 9:
        prop = width // 16
    else:
        prop = height // 9

    new_w = 16 * prop
    new_h = 9  * prop

    if min_x > width - new_w:
        x1 = width - new_w
    elif max_x < new_w:
        x1 = 0
    else:
        mid = (max_x - min_x) / 2
        x1 = min_x if (FinalMin(box_dict, mid, True)) else max_x - new_w

    if min_y > height - new_h:
        y1 = height - new_h
    elif max_y < new_h:
        y1 = 0
    else:
        mid = (max_y - min_y) / 2
        y1 = min_y if (FinalMin(box_dict, mid, False)) else max_y - new_h

    x2 = x1 + new_w
    y2 = y1 + new_h

    size = (x1, y1, x2, y2)
    new_image = image.crop(size)

    box_resize = []
    for boxx in box:
        boxx[0] = str(int(boxx[0]) - x1)
        boxx[1] = str(int(boxx[1]) - y1)
        boxx[2] = str(int(boxx[2]) - x1)
        boxx[3] = str(int(boxx[3]) - y1)
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
    """
    看原xml中的box
    :param xml_name: xml文件名
    :return:
    """
    etree = ET.parse(xml_name)
    root = etree.getroot()
    box = []
    box_dict = {}
    for obj in root.iter('object'):
        xmin,ymin,xmax,ymax = (x.text for x in obj.find('bndbox'))
        box.append([xmin,ymin,xmax,ymax])
        box_dict.update({p(obj.find('name').text):(xmin,ymin,xmax,ymax)})
    return box, box_dict

def write_xml(xml_name,save_name, box, resize_w, resize_h):
    """
    将修改后的box 写入到 xml文件中
    :param xml_name: 原xml
    :param save_name: 保存的xml
    :param box: 修改后需要写入的box
    :return:
    """
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
    """
    程序开始的主函数
    :param sourceDir: 源文件夹
    :param targetDir: 保存文件夹
    :param resize_w: 改变后的宽度
    :param resize_h: 改变后的高度
    :return:
    """
    if not os.path.exists(targetDir):
        os.makedirs(targetDir)

    for root, dirs, filenames in os.walk(sourceDir):
        for d in dirs:
            if not os.path.exists(os.path.join(targetDir, d)):
                curtar = os.makedirs(os.path.join(targetDir, d))
            curtar = os.path.join(targetDir, d)
            for filename in os.listdir(os.path.join(sourceDir, d)):
                file = os.path.splitext(filename)[0]
                if os.path.splitext(filename)[1] == '.jpg':
                    print('正在进行crop:' + filename)
                    filename_jpg = os.path.join(root, d, filename)
                    xml_name = os.path.join(root, d, file + '.xml')
                    box, box_dict = read_xml(xml_name)
                    image_data, box_data = CropImage(filename_jpg, box, box_dict)
                    resize_w, resize_h = image_data.size
                    image_data.save(os.path.join(curtar, filename))

                    for j in range(len(box_data)):
                        thickness = 3
                        left, top, right, bottom = box_data[j][0:4]
                        draw = ImageDraw.Draw(image_data)
                        for i in range(thickness):
                            draw.rectangle([int(left) + i, int(top) + i, int(right) - i, int(bottom) - i], outline=(255, 0, 0))

                    # 修改xml文件（将修改后的 box 写入到xml文件中）
                    save_xml = os.path.join(curtar, file + '.xml')
                    write_xml(xml_name, save_xml, box_data, resize_w, resize_h)
                    # 查看box绘制在图片上的效果
                    path = os.path.join('../' + curtar + '_draw')
                    if not os.path.exists(path):
                        os.makedirs(path)
                    image_data.save(os.path.join(path, filename))

if __name__ == "__main__":

    # 源文件夹
    sourceDir = "../low"
    # 结果保存文件夹
    targetDir = "../result"

    start(sourceDir, targetDir)
    print('完成！')




