import os
import shutil
import pandas as pd
from wxauto import WeChat
from datetime import datetime, timedelta
from logger import logger
from database import save_checkin_record
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

wx = WeChat()

# 新增月历标记功能
CALENDAR_POSITIONS = {
    # 示例格式：需要根据实际图片坐标填写
    # 每月日期坐标示例（需按实际图片调整）
    6: {i: (240 + (i%7)*82, 1185 + (i//7)*75) for i in range(1, 31)},
    7: {i: (240 + (i%7)*82, 1185 + (i//7)*75) for i in range(1, 32)},
    # ...其他月份
}

# CALENDAR_POSITIONS = {
#     1: {
#         1: (100, 150), 2: (130, 150), 3: (160, 150),
#         # ...完整配置1月日期坐标
#     },
#     2: {
#         1: (110, 140), 2: (140, 140), 3: (170, 140),
#         # ...完整配置2月日期坐标
#     },
#     # ...其他月份配置
# }

def mark_all_user_checkins(group_name, user_id, month=None):
    """
    标记指定用户在指定月份的所有打卡记录
    :param group_name: 群组名称
    :param user_id: 用户ID
    :param month: 月份（默认当前月份）
    :return: 生成的图片路径
    """
    try:
        # 获取当前日期信息
        now = datetime.now()
        target_month = month or now.month
        target_year = now.year if month <= now.month else now.year - 1 if month > now.month and now.month < 12 else now.year
        
        # 读取打卡记录
        file_path = f'./data/checkin/checkin_records_{group_name}.csv'
        if not os.path.exists(file_path):
            return None
            
        df = pd.read_csv(file_path)
        df['checkin_time'] = pd.to_datetime(df['checkin_time'])
        
        # 筛选目标记录
        user_records = df[df['user_id'] == user_id]
        if target_month:
            user_records = user_records[user_records['checkin_time'].dt.month == target_month]
        
        # 获取对应日期
        marked_days = [d.date().day for d in user_records['checkin_time']]
        
        if not marked_days:
            logger.info(f"🔍 {user_id} 在 {target_month} 月无打卡记录")
            return None
            
        # 生成日历标记
        return batch_mark_calendar(group_name, target_month, marked_days)
            
    except Exception as e:
        logger.exception("❌ 批量标记失败", exc_info=True)
        return None

def batch_mark_calendar(group_name, month, days):
    """批量标记日历日期"""
    image_dir = os.path.join('calendars', group_name)
    os.makedirs(image_dir, exist_ok=True)
    
    image_path = os.path.join(image_dir, f'{month}.jpg')
    
    # 如果图片不存在则复制模板
    template_path = os.path.join('templates', 'calendar_template.jpg')
    if os.path.exists(template_path):
        shutil.copy(template_path, image_path)
    else:
        logger.error("❌ 缺少日历模板图片")
        return None

    try:
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)
        
        # 创建字体对象（系统字体路径或自定义字体）
        try:
            font = ImageFont.truetype("arial.ttf", 24)  # Windows常用字体
        except:
            font = ImageFont.load_default()  # 回退到默认字体

        for day in days:
            if month not in CALENDAR_POSITIONS or day not in CALENDAR_POSITIONS[month]:
                logger.warning(f"⚠️ 未配置{month}月{day}日坐标")
                continue
                
            x, y = CALENDAR_POSITIONS[month][day]
            # radius = 6
            # draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill='red')
            radius = 18
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                outline='red',   # 轮廓颜色
                width=2          # 轮廓线宽
            )
            
            # 绘制"✔"符号（代替原来的圆形）
            # draw.text(
            #     (x, y), 
            #     "✔", 
            #     fill='red',  # 保持原有颜色
            #     font=font,
            #     anchor="mm"  # 居中对齐
            # )
        
        image.save(image_path)
        logger.info(f"✅ 已批量标记{month}月{len(days)}个日期")
        return image_path
        
    except Exception as e:
        logger.exception("❌ 批量绘制失败", exc_info=True)
        return None
            
    

def calculate_continuous_days(df, user_id):
    user_records = df[df['user_id'] == user_id].sort_values(by='checkin_time', ascending=False)

    if not user_records.empty:
        last_checkin_date = pd.to_datetime(user_records.iloc[0]['checkin_time']).date()
        last_continuous_days = int(user_records.iloc[0]['continuous_days'])

        today = datetime.now().date()

        days_diff = (today - last_checkin_date).days

        if days_diff == 1:
            return last_continuous_days + 1
        elif days_diff > 1:
            return 1
        else:
            return last_continuous_days
    else:
        return 1

def handle_checkin(msg, chat):
    try:
        now = datetime.now()
        today = now.date()
        user_id = msg.sender
        group_name = chat.who  # 获取当前聊天窗口（群名）
        file_path = f'./data/checkin/checkin_records_{group_name}.csv'

        logger.debug(f"💾 准备写入打卡记录至: {file_path}")

        # 创建目录（如果不存在）
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 读取现有打卡记录
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df['checkin_time'] = pd.to_datetime(df['checkin_time'])
        else:
            df = pd.DataFrame(columns=['user_id', 'checkin_time', 'continuous_days'])

        # 查询今日是否已打卡
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        user_today = df[
            (df['user_id'] == user_id) &
            (df['checkin_time'] >= today_start) &
            (df['checkin_time'] <= today_end)
        ]

        if not user_today.empty:
            msg.reply('今日已打卡')
            logger.debug("⚠️ 用户今日已打卡")
            return

        checkin_time = now.strftime('%Y-%m-%d %H:%M:%S')

        continuous_days = calculate_continuous_days(df, user_id)

        new_record = pd.DataFrame({
            'user_id': [user_id],
            'checkin_time': [checkin_time],
            'continuous_days': [continuous_days]
        })

        file_exists = os.path.isfile(file_path)
        new_record.to_csv(file_path, mode='a', header=not file_exists, index=False)

        # 获取当前日期
        now = datetime.now()
        current_month = now.month
        current_day = now.day
        
        # 批量标记所有打卡记录
        image_path = mark_all_user_checkins(group_name, user_id, current_month)

        # 发送图片（如果存在）
        if image_path and os.path.exists(image_path):
            try:
                # 调用微信发送文件接口（具体方法可能需要调整）
                # chat.send_file(image_path)
                wx.SendFiles(filepath=image_path, who=chat.who, exact=False)

                # reply_text += "\n📎 已更新月历标记"
                logger.info("📎 日历图片已发送")
            except Exception as e:
                logger.error(f"❌ 发送图片失败: {str(e)}")


        logger.info(f"✅ 打卡成功: {user_id}, 连续打卡: {continuous_days} 天")

        msg.reply(f'{user_id} 打卡成功！时间：{checkin_time}，已连续打卡 {continuous_days} 天')

    except Exception as e:
        logger.exception("❌ 执行打卡时发生异常", exc_info=True)
        msg.reply("系统错误，请稍后再试")