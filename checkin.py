import os
import pandas as pd
from datetime import datetime, timedelta
from logger import logger


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

        logger.info(f"✅ 打卡成功: {user_id}, 连续打卡: {continuous_days} 天")

        msg.reply(f'{user_id} 打卡成功！时间：{checkin_time}，已连续打卡 {continuous_days} 天')

    except Exception as e:
        logger.exception("❌ 执行打卡时发生异常", exc_info=True)
        msg.reply("系统错误，请稍后再试")