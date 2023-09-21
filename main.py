from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from iqoptionapi.stable_api import IQ_Option
import time

class TradingApp(App):
    def build(self):
        self.title = "Trading App"
        self.root = BoxLayout(orientation='vertical', padding=10)

        # IQ Option login inputs
        self.email_input = TextInput(hint_text="Enter IQ Login Email")
        self.password_input = TextInput(hint_text="Enter IQ Login Password", password=True)
        self.login_button = Button(text="Log In")
        self.login_button.bind(on_press=self.login)

        # Trading settings inputs
        self.initial_amount_input = TextInput(hint_text="Initial Stack Amount")
        self.martingale_factor_input = TextInput(hint_text="Martingale Multiplier")
        self.martingale_step_input = TextInput(hint_text="Martingale Step")
        self.currency_pair_input = TextInput(hint_text="Currency Pair (e.g., EURUSD)")
        self.expiry_time_input = TextInput(hint_text="Expiry Time (minutes)")
        self.trade_times_input = TextInput(hint_text="Trade Times (HH:MM:SS,HH:MM:SS,...)")
        self.trade_types_input = TextInput(hint_text="Trade Types (call,put,call,...)")
        self.next_signal_marti_input = Spinner(text="Next Signal Martingale Continue", values=["Y", "N"])
        self.start_trading_button = Button(text="Start Trading")
        self.start_trading_button.bind(on_press=self.start_trading)

        # Output label
        self.output_label = Label(text="")

        self.root.add_widget(self.email_input)
        self.root.add_widget(self.password_input)
        self.root.add_widget(self.login_button)
        self.root.add_widget(self.initial_amount_input)
        self.root.add_widget(self.martingale_factor_input)
        self.root.add_widget(self.martingale_step_input)
        self.root.add_widget(self.currency_pair_input)
        self.root.add_widget(self.expiry_time_input)
        self.root.add_widget(self.trade_times_input)
        self.root.add_widget(self.trade_types_input)
        self.root.add_widget(self.next_signal_marti_input)
        self.root.add_widget(self.start_trading_button)
        self.root.add_widget(self.output_label)

        return self.root

    def login(self, instance):
        email = self.email_input.text
        password = self.password_input.text
        self.Iq = IQ_Option(email, password)
        iqch1, iqch2 = self.Iq.connect()
        if iqch1:
            self.output_label.text = "Log In Successful."
        else:
            self.output_label.text = "Log In failed."

    def start_trading(self, instance):
        if not hasattr(self, 'Iq'):
            self.output_label.text = "Please log in first."
            return

        try:
            self.INITIAL_AMOUNT = float(self.initial_amount_input.text)
            self.MARTINGALE_FACTOR = float(self.martingale_factor_input.text)
            self.MARTINGALE_STEP = int(self.martingale_step_input.text)
            self.instrument_id = self.currency_pair_input.text.upper()
            self.expirations_mode = int(self.expiry_time_input.text)
            self.trade_times_input_text = self.trade_times_input.text
            self.trade_types_input_text = self.trade_types_input.text
            self.next_signal_marti = self.next_signal_marti_input.text

            self.amount = self.INITIAL_AMOUNT
            self.MARTINGALE_COUNT = 0
            self.my_blc = self.Iq.get_balance()

            self.output_label.text = f"Balance: {self.my_blc}"
            self.trade_times = self.trade_times_input_text.split(",")  # Split trade times
            self.trade_types = self.trade_types_input_text.split(",")  # Split trade types
            Clock.schedule_interval(self.trade_loop, 1)  # Start trading loop
        except ValueError:
            self.output_label.text = "Invalid input. Please check your settings."

    def place_trade(self, trade_type):
        response, order_id = self.Iq.buy(self.amount, self.instrument_id, trade_type, self.expirations_mode)

        if response:
            self.output_label.text = f"Trade placed successfully! Trade ID: {order_id}"
            time.sleep(5)

            trade_result = self.Iq.check_win_v3(order_id)
            if trade_result > 0:
                self.output_label.text = "Trade result: Win!"
                self.MARTINGALE_COUNT = 0
                self.amount = self.INITIAL_AMOUNT
            else:
                self.output_label.text = "Trade result: Loss."
                self.MARTINGALE_COUNT += 1
                if self.MARTINGALE_COUNT <= self.MARTINGALE_STEP:
                    self.amount *= self.MARTINGALE_FACTOR
                    response, order_id = self.Iq.buy(self.amount, self.instrument_id, trade_type, self.expirations_mode)
                    self.output_label.text = f"Martingale trade placed: {self.amount}"
                else:
                    if self.next_signal_marti == "Y":
                        self.amount *= self.MARTINGALE_FACTOR
                    else:
                        self.amount = self.INITIAL_AMOUNT

    def trade_loop(self, dt):
        current_time = time.strftime("%H:%M:%S", time.localtime())

        if current_time in self.trade_times:
            index = self.trade_times.index(current_time)
            trade_type = self.trade_types[index]
            self.place_trade(trade_type)
            self.trade_times.remove(current_time)
            self.trade_types.pop(index)

            if not self.trade_times:
                new_bal = self.Iq.get_balance()
                profit = new_bal - self.my_blc
                self.output_label.text = f"Updated Balance: {new_bal}\nTotal Profit: {round(profit, 2)}"
                Clock.unschedule(self.trade_loop)  # Stop trading loop

if __name__ == '__main__':
    TradingApp().run()
