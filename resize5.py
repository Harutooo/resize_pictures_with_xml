import math
import os
import sys
from turtle import width
from unittest import result
from PIL import Image, ImageDraw
import numpy as np
import xml.etree.ElementTree as ET
from pandas import wide_to_long
import shutil

'''
设置收益函Gain, 表示当前剪裁框的的分数
权重参数w与体积比p
loss = p*w sum
'''
w = 0.9  #the weight of signs 

'''
为了生成可重复key的字典, 对象可以重复
'''
class p(object):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name
    def __str__(self):
        return self.name

'''
@brief  计算某个窗口的收益
@param1 box_dict    标注文件框
@param2 crop_win    当前剪裁窗口
@return 分数
'''
def Gain(box_dict, crop_win):
    gain = 0        # 初始化得分

    # abtr： 标注框类型； box： 标注框的坐标信息
    for abtr, box in box_dict.items():

        # 保证标注正确
        if int(box[0]) < crop_win[2] and int(box[1]) < crop_win[3] and int(box[2]) > crop_win[0] and int(box[3]) > crop_win[1] and int(box[0]) != int(box[2]) and int(box[1]) != int(box[3]): 
            xlist = [int(box[0]),int(box[2]),crop_win[0], crop_win[2]]
            ylist = [int(box[1]),int(box[3]),crop_win[1], crop_win[3]]
            xlist.sort()
            ylist.sort()
            x1, x2 = xlist[1], xlist[2]
            y1, y2 = ylist[1], ylist[2]

            squre_merge = (x2 - x1) * (y2 - y1)
            squre_box = (int(box[2]) - int(box[0])) * (int(box[3]) - int(box[1]))
            gain = gain + (squre_merge / squre_box) * (w if str(abtr).split('_')[0] == 'sign' else 1 - w)
    return gain

def CropImage(filename_jpg, box, box_dict):

    #  读取图像并转换成RGB图像
    image = Image.open(filename_jpg)
    image = image.convert('RGB')
    
    width, height = image.size
    if width / 16 == height / 9:
        return image, box, False

    prop = width // 16 if width / 16 < height / 9 else height // 9
    new_w = 16 * prop
    new_h = 9  * prop

    # set a initial crop window
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
    x2, y2 = x1 + new_w, y1 + new_h
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
        # boxx[0] = str(0)     if int(boxx[0]) - x1 < 0 else str(int(boxx[0]) - x1)
        # boxx[1] = str(0)     if int(boxx[1]) - y1 < 0 else str(int(boxx[1]) - y1)
        # boxx[2] = str(new_w) if int(boxx[2]) - new_w > 0 else str(int(boxx[2]) - new_w)
        # boxx[3] = str(new_h) if int(boxx[3]) - new_h > 0 else str(int(boxx[3]) - new_h)
        box_resize.append(boxx)
    return new_image, box_resize, True

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
def write_xml(xml_name,save_name, box, resize_w, resize_h):
    etree = ET.parse(xml_name)
    root = etree.getroot()

    # 修改图片的宽度、高度
    for obj in root.iter('size'):
        obj.find('width').text  = str(resize_w)
        obj.find('height').text = str(resize_h)

    for obj, bo in zip(root.findall('object'), box):
        # xmin,ymin,xmax,ymax = (x.text for x in obj.find('bndbox'))
        xmin,ymin,xmax,ymax = (x for x in bo)
        if int(xmin) >= int(xmax) or int(ymin) >= int(ymax) or int(xmin) >= resize_w or int(ymin) >= resize_h or int(xmax) <= 0 or int(ymax) <= 0:
            root.remove(obj)
        else:
            for index, x in enumerate(obj.find('bndbox')):
                x.text = bo[index]
    # print('box = ')
    # print(box)
    
    # for obj, bo in zip(root.iter('object'), box):
    #     for index, x in enumerate(obj.find('bndbox')):
    #         x.text = bo[index]
    etree.write(save_name)

def Enlerge(box_data, p):
    box = []
    for boxx in box_data:
        boxx[0] = str(int(int(boxx[0]) * p))
        boxx[1] = str(int(int(boxx[1]) * p))
        boxx[2] = str(int(int(boxx[2]) * p))
        boxx[3] = str(int(int(boxx[3]) * p))
        box.append(boxx)
    return box


def start(sourceDir, targetDir):
    for root, _, filenames in os.walk(sourceDir):
        for filename in filenames:
            file = os.path.splitext(filename)[0]
            if os.path.splitext(filename)[1] == '.jpg':
                print('正在进行crop:' + filename)
                filename_jpg = os.path.join(root, filename)
                xml_name = os.path.join(root, file + '.xml')
                box, box_dict = read_xml(xml_name)
                image_data, box_data, need_to_crop = CropImage(filename_jpg, box, box_dict)
                resize_w, resize_h = image_data.size

                if (resize_h < 720):
                    # 按比例修改box_data
                    p = 720 / resize_h
                    resize_w, resize_h = 1280, 720
                    image_data = image_data.resize((resize_w,resize_h))
                    box_data = Enlerge(box_data, p)
                image_data.save(os.path.join(targetDir, filename))
                save_xml = os.path.join(targetDir, file + '.xml')
                if need_to_crop or resize_h < 720:
                    # 修改xml文件（将修改后的 box 写入到xml文件中）
                    write_xml(xml_name, save_xml, box_data, resize_w, resize_h)
                else:
                    shutil.copy(xml_name, save_xml)
                    print ("copy %s -> %s"%(xml_name, save_xml))


if __name__ == "__main__":

    # 源文件夹
    sourceDir = "jpg"
    # 结果保存文件夹
    targetDir = "new_result"
    # 新建保存文件夹

    for dir1 in os.listdir(sourceDir):
        for dir2 in os.listdir(os.path.join(sourceDir, dir1)):
            now_source = os.path.join(sourceDir, dir1, dir2, '0')
            now_target = os.path.join(targetDir, dir1, dir2, '0')
            if not os.path.exists(now_target):
                os.makedirs(now_target)
            start(now_source, now_target)
            print('{}/{} 完成！'.format(dir1, dir2))
        print('{} 完成！'.format(dir1))
    
    # # 源文件夹
    # sourceDir = "test/test/"
    # # 结果保存文件夹
    # targetDir = "test/result"
    # start(sourceDir, targetDir)
    # # 新建保存文件夹

    print('完成！')
