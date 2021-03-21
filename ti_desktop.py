#!/usr/bin/python
import ti_config as cfg
import ti
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango, GLib
import cairo
import requests
import html
from rich.console import Console
from operator import itemgetter
import random
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_gtk3agg import (FigureCanvasGTK3Agg as FigureCanvas)
from matplotlib.figure import Figure

console = Console()

class TinkoffInvestDesktop(Gtk.Window):

    def __init__(self):
        super(TinkoffInvestDesktop, self).__init__()
        self.portfolio = self.get_portfolio()
        self.setup()
        self.init_ui()


    def setup(self):

        self.set_app_paintable(True)
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.set_keep_below(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual != None and screen.is_composited():
            self.set_visual(visual)

    def formatPrice(self, value, currency):
        currency_sign = {"RUB":'₽',"USD":"$","EUR":"€"}
        return "{:,.0f} {}".format(value, currency_sign[currency]).replace(","," ")

    def getLabel(self, text, font, color, align):
        lbl = Gtk.Label()
        lbl.set_markup(text)
        fd = Pango.FontDescription(font)
        lbl.modify_font(fd)
        lbl.modify_fg(Gtk.StateFlags.NORMAL,Gdk.color_parse(color))
        lbl.set_halign(align)
        return lbl

    def redrawPortfolio(self):
        #console.print("Start update portfolio...")
        self.portfolio = self.get_portfolio()
        self.box.destroy()
        self.init_ui()
        #console.print("End update portfolio...")
        pass

    def cb_drag_start(self, widget, event):
        self.drag =  True
    
    def cb_drag(self,widget,event):
        if self.drag:
            self.move(math.floor(event.x_root) - 10, math.floor(event.y_root) - 10)

    def cb_drag_end(self, widget, event):
        self.drag =  False

    def callback_close(self, event, data):
        Gtk.main_quit()
        pass

    def init_ui(self):
        self.connect("draw", self.on_draw)
        self.box = Gtk.VBox()
        self.add(self.box)

        headBox = Gtk.HBox()

        self.eventBox = Gtk.EventBox()
        self.labelTitle = self.getLabel("Tinkoff Invest","Play Regular 40", "white", Gtk.Align.START)
        self.eventBox.add(self.labelTitle)
        self.eventBox.connect("button-press-event", self.cb_drag_start)
        self.eventBox.connect("motion-notify-event", self.cb_drag)
        self.eventBox.connect("button-release-event", self.cb_drag_end)
        headBox.pack_start(self.eventBox, True, True, 0)

        closeEventBox = Gtk.EventBox()
        closeLabelBtn = self.getLabel("×","Play Regular 40", "white", Gtk.Align.END)
        closeEventBox.add(closeLabelBtn)
        closeEventBox.connect("button-press-event", self.callback_close)
        headBox.pack_start(closeEventBox, True, True, 0)

        self.box.pack_start(headBox, True, True, 0)

        portfolio = self.portfolio
        
        summaryBox = Gtk.HBox()

        lbl_total = self.getLabel(self.formatPrice(portfolio["totalPortfolioSumRUB"],"RUB"),
            "Play Regular 20", "white", Gtk.Align.START)
        summaryBox.pack_start(lbl_total, False, False, 5)

        lbl_total = self.getLabel(self.formatPrice(portfolio["totalPortfolioProfitRUB"],"RUB"),
            "Play Regular 15", "#888888", Gtk.Align.START)
        summaryBox.pack_start(lbl_total, False, False, 5)
        
        self.box.pack_start(summaryBox, True, True, 0)

        portfolioBox = Gtk.HBox()
        portfolioTickersBox = Gtk.VBox()
        portfolioNamesBox = Gtk.VBox()
        portfolioBalancesBox = Gtk.VBox()
        portfolioPricesBox = Gtk.VBox()
        portfolioTotalsBox = Gtk.VBox()
        portfolioProfitsBox = Gtk.VBox()
        portfolioPercentsBox = Gtk.VBox()

        for item in portfolio["items"]:
            
            ###################################### ticker
            lbl = self.getLabel(f"<span background=\"#fff\" foreground=\"#000000\"> {item['ticker']} </span>",
                "Play Regular 8", "white", Gtk.Align.START)
            portfolioTickersBox.pack_start(lbl, True, True, 1)
            ###################################### name
            lbl = self.getLabel("{}".format(html.escape(item['name'])), "Play Regular 8", "white", Gtk.Align.START)
            portfolioNamesBox.pack_start(lbl, True, True, 1)
            
            ###################################### balance
            txt = "{:,.0f}".format(item['balance']).replace(",","")
            lbl = self.getLabel(txt, "Play Regular 8", "white", Gtk.Align.END)
            portfolioBalancesBox.pack_start(lbl, True, True, 1)
            
            ###################################### price
            txt = self.formatPrice(item["price"],item["priceCurrency"])
            lbl = self.getLabel(txt, "Play Regular 8", "white", Gtk.Align.END)
            portfolioPricesBox.pack_start(lbl, True, True, 1)

            ###################################### sum
            txt = self.formatPrice(item["totalPrice"],item["priceCurrency"])
            lbl = self.getLabel(txt, "Play Regular 8", "white", Gtk.Align.END)
            portfolioTotalsBox.pack_start(lbl, True, True, 1)

            ###################################### profit
            clr="white"
            if item["profit"] <= 0:
                clr = "#888888"
            txt = self.formatPrice(item["profit"],item["profitCurrency"])
            lbl = self.getLabel(txt, "Play Regular 8", clr, Gtk.Align.END)
            portfolioProfitsBox.pack_start(lbl, True, True, 1)

            ###################################### percents
            txt = "{:,.2f}%".format(item['percent']).replace(",","")
            lbl = self.getLabel(txt, "Play Regular 8", "white", Gtk.Align.END)
            portfolioPercentsBox.pack_start(lbl, True, True, 1)

        portfolioBox.pack_start(portfolioTickersBox, expand=True, fill=True, padding=5)
        portfolioBox.pack_start(portfolioNamesBox, expand=True, fill=True, padding=5)
        portfolioBox.pack_start(portfolioBalancesBox, expand=True, fill=True, padding=5)
        portfolioBox.pack_start(portfolioPricesBox, expand=True, fill=True, padding=5)
        portfolioBox.pack_start(portfolioTotalsBox, expand=True, fill=True, padding=5)
        portfolioBox.pack_start(portfolioProfitsBox, expand=True, fill=True, padding=5)
        portfolioBox.pack_start(portfolioPercentsBox, expand=True, fill=True, padding=5)

        self.box.pack_start(portfolioBox, expand=True, fill=True, padding=0)

        self.draw_piechart()

        self.resize(10, 10)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.move(200,30)
        self.connect("delete-event", Gtk.main_quit)
        self.show_all()
        GLib.timeout_add(cfg.portfolioUpdateInterval, self.redrawPortfolio)

    def draw_piechart(self):

        labels = []
        sizes = []
        colors = ['#ffffff','#dddddd','#bbbbbb', '#999999', '#777777', '#555555']

        i = 0
        other_percent = 0
        for item in self.portfolio["items"]:
            if i<5:
                labels.append(" " + item['ticker'] + " ") 
                sizes.append(item['percent'])
            else:
                other_percent += item['percent']
            i+=1

        if other_percent > 0:
            labels.append(" другие ")
            sizes.append(other_percent)
        
        fig, ax = plt.subplots()
        
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(0)

        wedges, text, autotext = ax.pie(sizes, colors = colors, labels=labels, autopct='%1.1f%%', startangle=0)
        plt.setp( wedges, width=0.25)
        #plt.setp( wedges, )

        for w in wedges:
            w.set_linewidth(1)
            w.set_linestyle('-')
            w.set_edgecolor('#555555')
            w.set_capstyle('projecting')

        fig = plt.gcf()
        ax.axis('equal') 
        
        for t in text:
            t.set_color("#999999")
            #t.set_backgroundcolor("white")
            t.set_fontname("Play")
            t.set_fontsize(8)
        
        for t in autotext:
            t.set_color("#888888")
            t.set_fontname("Play")
            t.set_fontsize(7)

        
        canvas = FigureCanvas(fig) 
        canvas.set_size_request(300,300)

        self.box.pack_start(canvas, expand=False, fill=True, padding=0)


    def on_draw(self, wid, cr):

        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

    def get_portfolio(self):
        self.portfolio = ti.get_portfolio_calculated()
        return self.portfolio

def main():

        app = TinkoffInvestDesktop()
        Gtk.main()


if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
