import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from math import ceil
import os

SAMPLING_POINTS = 101
KEYS = ["reno", "cubic", "yeah", "vegas"]

cwndDict04 = {"reno": [0] * SAMPLING_POINTS, "cubic": [0] * SAMPLING_POINTS, "yeah": [0] * SAMPLING_POINTS,
              "vegas": [0] * SAMPLING_POINTS}
cwndDict15 = {"reno": [0] * SAMPLING_POINTS, "cubic": [0] * SAMPLING_POINTS, "yeah": [0] * SAMPLING_POINTS,
              "vegas": [0] * SAMPLING_POINTS}

goodputDict04 = {"reno": [0] * SAMPLING_POINTS, "cubic": [0] * SAMPLING_POINTS, "yeah": [0] * SAMPLING_POINTS,
                 "vegas": [0] * SAMPLING_POINTS}
goodputDict15 = {"reno": [0] * SAMPLING_POINTS, "cubic": [0] * SAMPLING_POINTS, "yeah": [0] * SAMPLING_POINTS,
                 "vegas": [0] * SAMPLING_POINTS}

rttDict04 = {"reno": [0] * SAMPLING_POINTS, "cubic": [0] * SAMPLING_POINTS, "yeah": [0] * SAMPLING_POINTS,
             "vegas": [0] * SAMPLING_POINTS}

rttDict15 = {"reno": [0] * SAMPLING_POINTS, "cubic": [0] * SAMPLING_POINTS, "yeah": [0] * SAMPLING_POINTS,
             "vegas": [0] * SAMPLING_POINTS}

lossDict04 = {"reno": [0] * SAMPLING_POINTS, "cubic": [0] * SAMPLING_POINTS, "yeah": [0] * SAMPLING_POINTS,
              "vegas": [0] * SAMPLING_POINTS}
lossDict15 = {"reno": [0] * SAMPLING_POINTS, "cubic": [0] * SAMPLING_POINTS, "yeah": [0] * SAMPLING_POINTS,
              "vegas": [0] * SAMPLING_POINTS}

def splitFile(filename):
    lines = []
    file = open(filename, 'r')
    line = file.readline()
    while line:
        lines.append(line.split())
        line = file.readline()
    return lines


def adjustArray(arr, defaultVal):
    for i in range(len(arr)):
        if arr[i] == defaultVal:
            arr[i] = arr[i - 1] if i != 0 else 0
    return arr


def splitCWND(data):
    cwnds04 = [-1] * SAMPLING_POINTS
    cwnds15 = [-1] * SAMPLING_POINTS
    for line in data:
        if 'cwnd_' in line:
            indexes = [0, 6]
            if line[1] == '0':
                cwnds04[ceil(float(line[0]))] = float(line[6])
            else:
                cwnds15[ceil(float(line[0]))] = float(line[6])
    cwnds04 = adjustArray(cwnds04, -1)
    cwnds15 = adjustArray(cwnds15, -1)
    return cwnds04, cwnds15


def splitAcks(data):
    acks04 = ['none'] * SAMPLING_POINTS
    acks15 = ['none'] * SAMPLING_POINTS
    for line in data:
        if 'ack_' in line:
            if line[1] == '0':
                acks04[ceil(float(line[0]))] = int(line[-1])
            else:
                acks15[ceil(float(line[0]))] = int(line[-1])
    return adjustArray(acks04, 'none'), adjustArray(acks15, 'none')


def splitloss(data):
    loss04 = [-1] * SAMPLING_POINTS
    lastloss04 = 0
    loss15 = [-1] * SAMPLING_POINTS
    lastloss15 = 0
    for line in data:
        if line[0] == 'd':
            if line[-4][0] == '0':
                lastloss04 += 1
                loss04[ceil(float(line[1]))] = lastloss04
            elif line[-4][0] == '1':
                lastloss15 += 1
                loss15[ceil(float(line[1]))] = lastloss15
    return adjustArray(loss04, -1), adjustArray(loss15, -1)


def splitRtt(data):
    rtt04 = [-1] * SAMPLING_POINTS
    rtt15 = [-1] * SAMPLING_POINTS
    for line in data:
        if 'rtt_' in line:
            if line[1] == '0':
                rtt04[ceil(float(line[0]))] = float(line[-1])
            else:
                rtt15[ceil(float(line[0]))] = float(line[-1])
    return adjustArray(rtt04, -1), adjustArray(rtt15, -1)


def addCwndDatas(renoData, cubicData, yeahData, vegasData):
    global cwndDict04, cwndDict15
    renoCwnds04, renoCwnds15 = splitCWND(renoData)
    cubicCwnds04, cubicCwnds15 = splitCWND(cubicData)
    yeahCwnds04, yeahCwnds15 = splitCWND(yeahData)
    vegasCwnds04, vegasCwnds15 = splitCWND(vegasData)

    for i in range(SAMPLING_POINTS):
        cwndDict04['reno'][i] += renoCwnds04[i]
        cwndDict04['cubic'][i] += cubicCwnds04[i]
        cwndDict04['yeah'][i] += yeahCwnds04[i]
        cwndDict04['vegas'][i] += vegasCwnds04[i]
        cwndDict15['reno'][i] += renoCwnds15[i]
        cwndDict15['cubic'][i] += cubicCwnds15[i]
        cwndDict15['yeah'][i] += yeahCwnds15[i]
        cwndDict15['vegas'][i] += vegasCwnds15[i]


def addGoodputDatas(renoData, cubicData, yeahData, vegasData):
    global goodputDict04, goodputDict15
    renoGoodputs04, renoGoodputs15 = splitAcks(renoData)
    cubicGoodputs04, cubicGoodputs15 = splitAcks(cubicData)
    yeahGoodputs04, yeahGoodputs15 = splitAcks(yeahData)
    vegasGoodputs04, vegasGoodputs15 = splitAcks(vegasData)

    for i in range(SAMPLING_POINTS):
        goodputDict04['reno'][i] += renoGoodputs04[i]
        goodputDict04['cubic'][i] += cubicGoodputs04[i]
        goodputDict04['yeah'][i] += yeahGoodputs04[i]
        goodputDict04['vegas'][i] += vegasGoodputs04[i]
        goodputDict15['reno'][i] += renoGoodputs15[i]
        goodputDict15['cubic'][i] += cubicGoodputs15[i]
        goodputDict15['yeah'][i] += yeahGoodputs15[i]
        goodputDict15['vegas'][i] += vegasGoodputs15[i]


def addRttDatas(renoData, cubicData, yeahData, vegasData):
    global rttDict04, rttDict15
    renoRtts04, renoRtts15 = splitRtt(renoData)
    cubicRtts04, cubicRtts15 = splitRtt(cubicData)
    yeahRtts04, yeahRtts15 = splitRtt(yeahData)
    vegasRtts04, vegasRtts15 = splitRtt(vegasData)

    for i in range(SAMPLING_POINTS):
        rttDict04['reno'][i] += renoRtts04[i]
        rttDict04['cubic'][i] += cubicRtts04[i]
        rttDict04['yeah'][i] += yeahRtts04[i]
        rttDict04['vegas'][i] += vegasRtts04[i]
        rttDict15['reno'][i] += renoRtts15[i]
        rttDict15['cubic'][i] += cubicRtts15[i]
        rttDict15['yeah'][i] += yeahRtts15[i]
        rttDict15['vegas'][i] += vegasRtts15[i]


def addlossDatas(renoData, cubicData, yeahData, vegasData):
    global lossDict04, lossDict15
    renoloss04, renoloss15 = splitloss(renoData)
    cubicloss04, cubicloss15 = splitloss(cubicData)
    yeahloss04, yeahloss15 = splitloss(yeahData)
    vegasloss04, vegasloss15 = splitloss(vegasData)

    for i in range(SAMPLING_POINTS):
        lossDict04['reno'][i] += renoloss04[i]
        lossDict04['cubic'][i] += cubicloss04[i]
        lossDict04['yeah'][i] += yeahloss04[i]
        lossDict04['vegas'][i] += vegasloss04[i]
        lossDict15['reno'][i] += renoloss15[i]
        lossDict15['cubic'][i] += cubicloss15[i]
        lossDict15['yeah'][i] += yeahloss15[i]
        lossDict15['vegas'][i] += vegasloss15[i]

def runOneEpoch():
    # os.system("ns renoCode.tcl")
    # os.system("ns cubicCode.tcl")
    # os.system("ns yeahCode.tcl")
    # os.system("ns vegasCode.tcl")

    renoData = splitFile('DropTail/renoTrace.tr')
    cubicData = splitFile('DropTail/cubicTrace.tr')
    yeahData = splitFile('DropTail/yeahTrace.tr')
    vegasData = splitFile('DropTail/vegasTrace.tr')

    addCwndDatas(renoData, cubicData, yeahData, vegasData)
    addGoodputDatas(renoData, cubicData, yeahData, vegasData)
    addRttDatas(renoData, cubicData, yeahData, vegasData)
    addlossDatas(renoData, cubicData, yeahData, vegasData)

def total_goodput_Mbps(ack_data):
    time = 100
    # the size is 1kb per packege
    mbps = (ack_data[-1] * 8000) / (time * 1e6)
    return mbps

def plr_pct(total_data, loos_data):
    # nuit is %
    if total_data != 0:
        plr = (loos_data / total_data) * 100
    else:
        plr = 0
    return plr

def jain_fairness(flows_throughput):
    """
    parameter flows_throughput is a list has throughput if 2 dicts
    example:[throughput of dict04, throughput of dict15]
    """
    if sum(flows_throughput) != 0:
        j = (sum(flows_throughput) ** 2) / (len(flows_throughput) * sum(xi ** 2 for xi in flows_throughput))
    else:
        j = 0
    return j

def throughput_stability(goodput_list):
    """
    use ack to estimate the throughput
    step means the step length 2 ack use to calculate the difference
    if step is too short, cov will be Incredibly high
    """
    step = 2
    throughput_list = [-1] * (SAMPLING_POINTS - 1)
    for i in range(len(goodput_list) - step):
        throughput_list[i] = (goodput_list[i + step] - goodput_list[i]) / step

    mean_throughput = np.mean(throughput_list)
    std_throughput = np.std(throughput_list)

    if mean_throughput != 0:
        cov = std_throughput / mean_throughput
    else:
        cov = 0

    return cov

def PartA_1():

    print("PartA.1" + ("=" * 40))

    # save result for figure
    goodput_values_04 = []
    goodput_values_15 = []
    plr_values_04 = []
    plr_values_15 = []

    print("--- total_goodput_Mbps ---")
    for i in KEYS:
        print(i + " " + "Dict04" + ": ", end="")
        goodput_04 = total_goodput_Mbps(goodputDict04[i])
        print(goodput_04)
        goodput_values_04.append(goodput_04)

        print(i + " " + "Dict15" + ": ", end="")
        goodput_15 = total_goodput_Mbps(goodputDict15[i])
        print(goodput_15)
        goodput_values_15.append(goodput_15)

    print("--- plr_pct ---")
    for i in KEYS:
        loos_data = lossDict04[i][-1]
        total_data = goodputDict04[i][-1] + loos_data
        plr_04 = round(plr_pct(total_data, loos_data), 3)
        print(i + " " + "Dict04" + ": ", end="")
        print(plr_04, "%")
        plr_values_04.append(plr_04)

        loos_data = lossDict15[i][-1]
        total_data = goodputDict15[i][-1] + loos_data
        plr_15 = round(plr_pct(total_data, loos_data), 3)
        print(i + " " + "Dict15" + ": ", end="")
        print(plr_15, "%")
        plr_values_15.append(plr_15)

    # 生成比较图表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # 子图1: Goodput比较
    x = np.arange(len(KEYS))
    width = 0.35

    bars1 = ax1.bar(x - width / 2, goodput_values_04, width, label='Flow 0-4', alpha=0.8, color='skyblue')
    bars2 = ax1.bar(x + width / 2, goodput_values_15, width, label='Flow 1-5', alpha=0.8, color='lightcoral')

    ax1.set_xlabel('TCP Algorithms', fontsize=12)
    ax1.set_ylabel('Goodput (Mbps)', fontsize=12)
    ax1.set_title('Goodput Comparison of TCP Algorithms', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([key for key in KEYS], fontsize=11)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3, axis='y')

    # 调整Y轴范围以更好地显示小值
    max_goodput = max(max(goodput_values_04), max(goodput_values_15))
    ax1.set_ylim(0, max_goodput * 1.15)

    # 在柱状图上添加更精确的数值标签
    for bar in bars1:
        height = bar.get_height()
        if height > 0.001:  # 只显示大于0.001的值
            ax1.text(bar.get_x() + bar.get_width() / 2., height + max_goodput * 0.01,
                     f'{height:.5f}', ha='center', va='bottom', fontsize=8)

    for bar in bars2:
        height = bar.get_height()
        if height > 0.001:  # 只显示大于0.001的值
            ax1.text(bar.get_x() + bar.get_width() / 2., height + max_goodput * 0.01,
                     f'{height:.5f}', ha='center', va='bottom', fontsize=8)

    # 子图2: PLR比较
    bars3 = ax2.bar(x - width / 2, plr_values_04, width, label='Flow 0-4', alpha=0.8, color='lightgreen')
    bars4 = ax2.bar(x + width / 2, plr_values_15, width, label='Flow 1-5', alpha=0.8, color='orange')

    ax2.set_xlabel('TCP Algorithms', fontsize=12)
    ax2.set_ylabel('Packet Loss Rate (%)', fontsize=12)
    ax2.set_title('Packet Loss Rate Comparison', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels([key for key in KEYS], fontsize=11)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3, axis='y')

    # 调整Y轴范围以更好地显示PLR
    max_plr = max(max(plr_values_04), max(plr_values_15))
    ax2.set_ylim(0, max_plr * 1.2 if max_plr > 0 else 5)  # 如果所有值都是0，设置上限为5%

    # 在柱状图上添加更精确的数值标签
    for bar in bars3:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2., height + max_plr * 0.02,
                 f'{height:.3f}%', ha='center', va='bottom', fontsize=9)

    for bar in bars4:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2., height + max_plr * 0.02,
                 f'{height:.3f}%', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig('PartA_1_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()

def PartA_2():
    print("PartA.2" + ("=" * 40))
    print("--- Jain’s fairness index ---")
    for i in KEYS:
        flows_throughput = [total_goodput_Mbps(goodputDict04[i]),total_goodput_Mbps(goodputDict15[i])]
        print(i+": ",end="")
        print(round(jain_fairness(flows_throughput), 4))

def PartA_3():
    print("PartA.3" + ("=" * 40))
    print("--- CoV ---")
    for i in KEYS:
        print(i + " " + "Dict04" + ": ", end="")
        COV_04 = throughput_stability(goodputDict04[i])
        print(round(COV_04,3))

        print(i + " " + "Dict15" + ": ", end="")
        COV_15 = throughput_stability(goodputDict15[i])
        print(round(COV_15,3))

        print(i + " " + "total" + ": ", end="")
        t = throughput_stability(list(np.array(goodputDict04[i]) + np.array(goodputDict15[i])))
        print(round(t, 3))
        print("\n")

def PartA():
    runOneEpoch()
    PartA_1()
    PartA_2()
    PartA_3()

PartA()