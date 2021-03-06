import io
import plotly.io as pio
import plotly.graph_objs as go
import opencryptobot.emoji as emo
import opencryptobot.utils as utl

from io import BytesIO
from telegram import ParseMode
from pytrends.request import TrendReq
from opencryptobot.ratelimit import RateLimit
from opencryptobot.plugin import OpenCryptoPlugin, Category


class Trends(OpenCryptoPlugin):

    DEFAULT_T = "today 5-y"

    def get_cmds(self):
        return ["tr", "trend"]

    @OpenCryptoPlugin.save_data
    @OpenCryptoPlugin.send_typing
    def get_action(self, bot, update, args):
        if not args:
            update.message.reply_text(
                text=f"Usage:\n{self.get_usage()}",
                parse_mode=ParseMode.MARKDOWN)
            return

        tf = str()
        for arg in args:
            if arg.startswith("t="):
                tf = arg.replace("t=", "")
                args.remove(arg)
                break

        if tf:
            if tf != "all":
                from datetime import datetime
                now = datetime.today()
                date = utl.get_date(now, tf)

                if not date:
                    update.message.reply_text(
                        text=f"{emo.ERROR} Timeframe not formated correctly",
                        parse_mode=ParseMode.MARKDOWN)
                    return
                else:
                    tf = f"{str(date)[:10]} {str(now)[:10]}"
        else:
            tf = self.DEFAULT_T

        if len(args) > 5:
            update.message.reply_text(
                text=f"{emo.ERROR} Not possible to provide more then 5 keywords",
                parse_mode=ParseMode.MARKDOWN)
            return

        if RateLimit.limit_reached(update):
            return

        try:
            pytrends = TrendReq(hl='en-US', tz=360)
            pytrends.build_payload(args, cat=0, timeframe=tf, geo='', gprop='')

            data = pytrends.interest_over_time()
        except Exception as e:
            return self.handle_error(e, update)

        some_data = None
        tr_data = list()
        for kw in args:
            tr_data.append(go.Scatter(x=data.get(kw).index, y=data.get(kw).values, name=kw))

            if not data.get(kw).empty:
                some_data = True

        if not some_data:
            update.message.reply_text(
                text=f"{emo.ERROR} No data for keyword(s): {', '.join(args)}",
                parse_mode=ParseMode.MARKDOWN)
            return

        layout = go.Layout(
            title="Google Trends - Interest Over Time",
            paper_bgcolor='rgb(233,233,233)',
            plot_bgcolor='rgb(233,233,233)',
            yaxis=dict(
                title="Queries",
                showticklabels=False),
            showlegend=True)

        try:
            fig = go.Figure(data=tr_data, layout=layout)
        except Exception as e:
            return self.handle_error(e, update)

        update.message.reply_photo(
            photo=io.BufferedReader(BytesIO(pio.to_image(fig, format="jpeg"))),
            parse_mode=ParseMode.MARKDOWN)

    def get_usage(self):
        return f"`/{self.get_cmds()[0]} <keyword> (<keyword> ... t=<# of>d|m|y)`"

    def get_description(self):
        return "Google Trends - Interest Over Time"

    def get_category(self):
        return Category.GENERAL
