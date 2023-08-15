import imgui
from imgui.integrations.glfw import GlfwRenderer

class GuiParameters:

    def __init__(self):
        self.checkbox1 = False
        self.checkbox2 = False

        self.year_start = 2023
        self.month_start = 3
        self.day_start = 3
        self.hour_start = 15

        self.year_end = 2023
        self.month_end = 3
        self.day_end = 4
        self.hour_end = 15

        self.color = [0.1,0.2,0.5,1]
        self.text_color = [1-self.color[0], 1-self.color[1], 1-self.color[2],1]
        self.gui_width = 310
        self.gui_height = 200
        self.single_date = True
        self.period = False

    def match(self):
        self.year_end = self.year_start
        self.month_end = self.month_start
        self.day_end = self.day_start
        self.hour_end = self.hour_start


class Gui:

    def __init__(self) -> None:
        pass

    def first_draw(self, impl:GlfwRenderer) -> None:
        window_with = impl.io.display_size.x
        gui_width = 312
        margin = 40
        impl.process_inputs()
        imgui.new_frame()
        imgui.set_next_window_size_constraints((gui_width,20), (gui_width, 1000))
        imgui.begin("DTCC Viewer", flags = imgui.WINDOW_ALWAYS_AUTO_RESIZE | imgui.WINDOW_NO_SAVED_SETTINGS)
        imgui.set_window_position_labeled("DTCC Viewer", window_with - (gui_width + margin), margin)

    def second_draw(self, guip:GuiParameters) -> None:
        self.styles(guip)                
        self.buttons_example(guip)       
        self.checkbox_example(guip)      
        self.add_dates_ui(guip)          
        self.apperance_settings(guip)     

    
    def third_draw(self, impl:GlfwRenderer) -> None:
        imgui.end()   
        imgui.render()
        impl.render(imgui.get_draw_data())
        imgui.end_frame()

    def styles(self, guip:GuiParameters) -> None:
        style = imgui.get_style()
        style.colors[imgui.COLOR_BORDER] = (0, 0.5, 1, 1)
        style.colors[imgui.COLOR_TITLE_BACKGROUND] = (0.5, 0.5, 0.5, 1)
        style.colors[imgui.COLOR_TITLE_BACKGROUND_ACTIVE] = (1, 0.5, 1, 0.5)
        style.colors[imgui.COLOR_BUTTON] = (0.3, 0.5, 1, 1)
        style.colors[imgui.COLOR_WINDOW_BACKGROUND] = (0.2, 0.2, 0.2, 0.3)
        style.colors[imgui.COLOR_TEXT] = (1-guip.color[0], 1-guip.color[1], 1-guip.color[2],1)

    def buttons_example(self, guip:GuiParameters) -> None:
        [expanded, visible] = imgui.collapsing_header("Buttons")
        if (expanded):       
            # Buttons to trigger action of some sort
            if(imgui.button("btn1!")):
                print("Pressed first btn")
            
            imgui.same_line()
            if(imgui.button("btn2!")):
                print("Pressed second btn")

            imgui.same_line()
            if(imgui.button("btn3!")):
                print("Pressed third btn")

        imgui.spacing()

    def checkbox_example(self, guip:GuiParameters) -> None:
        [expanded, visible] = imgui.collapsing_header("Checkboxes")
        if(expanded):
            # Check box to change settings
            [changed, guip.checkbox1] = imgui.checkbox("cbx1!", guip.checkbox1)
            imgui.same_line()
            [changed, guip.checkbox2] = imgui.checkbox("cbx2!", guip.checkbox2)
        
        imgui.spacing()

    def add_dates_ui(self, guip:GuiParameters) -> None:
        [expanded, visible] = imgui.collapsing_header("Date")

        if(expanded):
        
            if imgui.radio_button("date", guip.single_date):
                guip.period = guip.single_date
                guip.single_date = not guip.single_date

            imgui.same_line()   
            if imgui.radio_button("period", guip.period):
                guip.single_date = guip.period
                guip.period = not guip.period

            if guip.period:
                imgui.same_line()
                if imgui.button("match"):
                    guip.match()

            self.draw_bar(guip)
            
            # Sliders to change values
            [changed_year, guip.year_start] = imgui.slider_int("year_start", guip.year_start, 1990, 2023)
            [changed_month, guip.month_start] = imgui.slider_int("month_start", guip.month_start, 1, 12)
            [changed_day, guip.day_start] = imgui.slider_int("day_start", guip.day_start, 1, Gui.get_days_per_month(guip.year_start, guip.month_start))
            [changed_hour, guip.hour_start] = imgui.slider_int("hour_start", guip.hour_start, 0, 24)

            if(changed_month, changed_year):
                new_day = Gui.update_day(guip.year_start, guip.month_start, guip.day_start)
                guip.day_start = new_day
            
            # Add an other 
            if(guip.period):
                self.draw_bar(guip)
                [changed_year, guip.year_end] = imgui.slider_int("year_end", guip.year_end, 1990, 2023)
                [changed_month, guip.month_end] = imgui.slider_int("month_end", guip.month_end, 1, 12)
                [changed_day, guip.day_end] = imgui.slider_int("day_end", guip.day_end, 1, Gui.get_days_per_month(guip.year_end, guip.month_end))
                [changed_hour, guip.hour_end] = imgui.slider_int("hour_end", guip.hour_end, 0, 24)

                if(changed_month, changed_year):
                    new_day = Gui.update_day(guip.year_end, guip.month_end, guip.day_end)
                    guip.day_end = new_day
            self.draw_bar(guip)    

        imgui.spacing()

    def apperance_settings(self, guip:GuiParameters) -> None:
        [expanded, visible] = imgui.collapsing_header("Apperance")
        if(expanded):
            [changed, guip.color] = imgui.color_edit4("color", guip.color[0], guip.color[1],guip.color[2], guip.color[3])    

    def draw_bar(self, guip:GuiParameters) -> None:
        imgui.push_style_color(imgui.COLOR_TEXT, guip.text_color[0], guip.text_color[1], guip.text_color[2], 0.5)
        imgui.text("//////////////////////////////////////////")
        imgui.pop_style_color()

    @staticmethod
    def update_day(year:int, month:int, current_day:int) -> None:
        new_day = current_day
        days_per_month = Gui.get_days_per_month(year, month)

        if current_day > days_per_month:
            print(days_per_month)
            new_day = days_per_month
        
        return new_day

    @staticmethod
    def get_days_per_month(year:int, month:int) -> None:
        
        days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]        
        if (year % 4) == 0:
            days_per_month[1] = 29

        month_index = month-1
        return days_per_month[month_index]     