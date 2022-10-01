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
设置损失函Gain，表示当前剪裁框的的愤怒
权重参数w与体积比p
loss = p*w sum
'''
w = 0.9  #the weight of signs 

# 为了生成可重复key的字典， 对象可以重复
class p(object):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name
    def __str__(self):
        return self.name

def IsIn(small, big):
    res = True
    if small[0] >= big[2] or small[1] >= big[3] or small[2] <= big[0] or small[3] <= big[1]:
        res = False
    return res

# 判断当前剪裁框得分
def Gain(box_dict, crop_win):
    gain = 0
    for abtr, box in box_dict.items():
        box = list(map(int, box))
        if IsIn(box, crop_win): 
            # xlist = [int(box[0]),int(box[2]),crop_win[0], crop_win[2]]
            # ylist = [int(box[1]),int(box[3]),crop_win[1], crop_win[3]]
            xlist = [box[0],box[2],crop_win[0], crop_win[2]]
            ylist = [box[1],box[3],crop_win[1], crop_win[3]]
            xlist.sort()
            ylist.sort()
            x1, x2 = xlist[1], xlist[2]
            y1, y2 = ylist[1], ylist[2]

            squre_merge = (x2 - x1) * (y2 - y1)
            squre_box = (int(box[2]) - int(box[0])) * (int(box[3]) - int(box[1]))
            gain = gain + (squre_merge / squre_box) * (w if str(abtr).split('_')[0] == 'sign' else (1 - w))
    return gain

def CropImage(filename_jpg, box, box_dict):
    #   读取图像并转换成RGB图像
    image = Image.open(filename_jpg)
    image = image.convert('RGB')
    # 找出最小边界
    # 得到剪裁后的高宽
    width, height = image.size
    prop = width // 16 if width / 16 < height / 9 else height // 9
    new_w = 16 * prop
    new_h = 9  * prop

    x1, xbnd = 0, width  - new_w
    y1, ybnd = 0, height - new_h

    best = [x1, y1]
    stride = 5

    gain = 0
    while x1 < xbnd:
        list = [x1, 0, x1 + new_w, height]
        newgain = Gain(box_dict, list)
        if  newgain > gain:
            gain = newgain
            best[0] = x1
        x1 = x1 + stride

    gain = 0
    while y1 < ybnd:
        list = [best[0], y1, best[0] + new_w, y1 + new_h]
        newgain = Gain(box_dict, list)
        if  newgain > gain:
            gain = newgain
            best[1] = y1
        y1 = y1 + stride        

    x1, y1 = best[0], best[1]
    x2 = x1 + new_w
    y2 = y1 + new_h
    size = (x1, y1, x2, y2)
    new_image = image.crop(size)

    box_resize = []
    crop_win = [x1, y1, x2, y2]
    for boxx in box:
        boxx = list(map(int, boxx))
        if IsIn(boxx, crop_win):
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
    return new_image, box_resize, crop_win

"""
看原xml中的box
:param xml_name: xml文件名
:return:
"""
def read_xml(xml_name):
    etree = ET.parse(xml_name)
    root = etree.getroot()
    box = []
    box_dict = {}
    for obj in root.iter('object'):
        xmin,ymin,xmax,ymax = (x.text for x in obj.find('bndbox'))
        box.append([xmin,ymin,xmax,ymax])
        box_dict.update({p(obj.find('name').text):(xmin,ymin,xmax,ymax)})
    return box, box_dict

"""
将修改后的box 写入到 xml文件中
:param xml_name: 原xml
:param save_name: 保存的xml
:param box: 修改后需要写入的box
:return:
"""
def write_xml(xml_name,save_name, box, resize_w, resize_h, big_box):
    etree = ET.parse(xml_name)
    root = etree.getroot()

    # 修改图片的宽度、高度
    for obj in root.iter('size'):
        obj.find('width').text  = str(resize_w)
        obj.find('height').text = str(resize_h)
   
    for obj in root.iter('object'):
        xmin,ymin,xmax,ymax = (x.text for x in obj.find('bndbox'))
        box = [int(xmin), int(ymin), int(xmax), int(ymax)]
        # if int(xmin) >= resize_w or int(ymin) >= int(resize_h) or int(xmax) <= 0 or int(ymax) <= 0:
        if not(IsIn(box, big_box)):
            root.remove(obj)

    # 修改box的值
    for obj, bo in zip(root.iter('object'), box):
        for index, x in enumerate(obj.find('bndbox')):
            print(index)
            x.text = bo[index]
    etree.write(save_name)

"""
程序开始的主函数
:param sourceDir: 源文件夹
:param targetDir: 保存文件夹
:return:无
"""
def start(sourceDir, targetDir):
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
                    image_data, box_data, big_box = CropImage(filename_jpg, box, box_dict)
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
                    write_xml(xml_name, save_xml, box_data, resize_w, resize_h, big_box)
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
    # 新建保存文件夹
    if not os.path.exists(targetDir):
        os.makedirs(targetDir)
        
    start(sourceDir, targetDir)
    print('完成！')




