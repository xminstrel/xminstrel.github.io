import os

def verify_checksum(sentence):
    """
    验证 NMEA 语句的校验和是否正确
    """
    if not sentence.startswith('$') or '*' not in sentence:
        return False
    
    # 提取 '$' 和 '*' 之间的内容
    body_end_idx = sentence.rfind('*')
    body = sentence[1:body_end_idx]
    
    # 提取句子末尾提供的校验和
    provided_checksum = sentence[body_end_idx + 1:]
    
    # 计算校验和 (所有字符的异或值)
    calculated_checksum = 0
    for char in body:
        calculated_checksum ^= ord(char)
        
    # 将计算结果转为大写十六进制字符串，并与提供的校验和比较
    return f"{calculated_checksum:02X}" == provided_checksum.upper()

def format_time(utc_time):
    """格式化 UTC 时间 (hhmmss.sss -> hh:mm:ss.sss)"""
    if not utc_time or len(utc_time) < 6:
        return "未知时间"
    return f"{utc_time[0:2]}:{utc_time[2:4]}:{utc_time[4:6]}{utc_time[6:]}"

def format_date(utc_date):
    """格式化 UTC 日期 (ddmmyy -> 20yy-mm-dd)"""
    if not utc_date or len(utc_date) != 6:
        return "未知日期"
    return f"20{utc_date[4:6]}-{utc_date[2:4]}-{utc_date[0:2]}"

def parse_gga(parts):
    """解析 GGA 语句 (定位信息)"""
    time = format_time(parts[1])
    lat = parts[2] + parts[3] if parts[2] else "未知纬度"
    lon = parts[4] + parts[5] if parts[4] else "未知经度"
    fix_quality = parts[6]
    satellites = parts[7] if parts[7] else "0"
    
    status_map = {"0": "未定位", "1": "单点定位", "2": "差分定位"}
    status = status_map.get(fix_quality, "未知状态")
    
    print(f"[GGA 时间: {time}] 状态: {status} | 卫星数: {satellites} | 位置: {lat}, {lon}")

def parse_rmc(parts):
    """解析 RMC 语句 (推荐最小定位信息)"""
    time = format_time(parts[1])
    status = "有效(A)" if parts[2] == 'A' else "无效(V)"
    lat = parts[3] + parts[4] if parts[3] else "未知"
    lon = parts[5] + parts[6] if parts[5] else "未知"
    speed = parts[7] if parts[7] else "0.0"
    date = format_date(parts[9])
    
    print(f"[RMC 日期: {date} {time}] 信号状态: {status} | 速度: {speed}节 | 位置: {lat}, {lon}")

def process_nmea_file(file_path):
    """
    逐行读取并处理 NMEA 文件
    """
    if not os.path.exists(file_path):
        print(f"错误: 找不到文件 {file_path}")
        return

    print(f"--- 开始解析文件: {file_path} ---\n")
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # 过滤空行或非标准行
            if not line.startswith('$'):
                continue
                
            # 校验和验证
            if not verify_checksum(line):
                # print(f"警告: 第 {line_num} 行校验和错误 -> {line}")
                continue
                
            # 按逗号拆分字段
            parts = line.split(',')
            
            # 提取消息标识符 (例如 $GNGGA 中的 GGA)
            header = parts[0]
            if len(header) >= 6:
                msg_type = header[3:] # 截取后三个字符
                
                # 根据不同类型的语句进行分别处理
                if msg_type == 'GGA':
                    parse_gga(parts)
                elif msg_type == 'RMC':
                    parse_rmc(parts)

if __name__ == "__main__":
    # 替换为您实际的文件名
    nmea_file_path = "gps.nea"  
    
    # 创建一个测试文件用于演示 (可选)
    test_data = """$GNGGA,055933.085,,,,,0,0,,,M,,M,,*52
$GNRMC,055933.085,V,,,,,0.00,0.00,070180,,,N*59
$GNGGA,060030.085,,,,,0,0,,,M,,M,,*5D
$GNRMC,060030.085,V,,,,,0.00,0.00,230326,,,N*5D"""
    with open(nmea_file_path, "w") as f:
        f.write(test_data)
        
    # 运行解析
    process_nmea_file(nmea_file_path)