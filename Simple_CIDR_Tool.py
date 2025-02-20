from tkinter import ttk, filedialog, messagebox
from tkinter import END, CENTER, LEFT
from tkinter import Tk, Text, StringVar
from ipaddress import ip_network, collapse_addresses
from math import ceil, log2
from csv import writer
import os

# 设置 TCL_LIBRARY 和 TK_LIBRARY 环境变量
os.environ['TCL_LIBRARY'] = r'C:\Program Files\Python313\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = r'C:\Program Files\Python313\tcl\tk8.6'


class Utils:
    def __init__(self):
        pass

    # 格式化网络信息
    def format_network_info(self, network):
        info = f"CIDR: {network['cidr']}\n"
        info += f"协议版本: IPv{network['version']}\n"
        info += f"网络地址: {network['network_address']}\n"
        info += f"广播地址: {network['broadcast_address']}\n"
        info += f"子网掩码: {network['netmask']}\n"
        info += f"主机掩码: {network['hostmask']}\n"
        info += f"可用地址范围: {network['first_address']} - {network['last_address']}\n"
        info += f"所有地址总数: {network['num_addresses']}\n"
        info += f"可用地址总数: {network['host_addresses']}\n"
        return info

    # 获取单个子网信息
    def get_single_subnet_info(self, subnet):
        subnet_info = {
            "cidr": "",
            "version": "",
            "network_address": "",
            "broadcast_address": "",
            "netmask": "",
            "hostmask": "",
            "first_address": "",
            "last_address": "",
            "num_addresses": "",
            "host_addresses": ""
        }
        try:
            network = ip_network(f"{subnet}", strict=False)
        except ValueError as e:
            return f"[ {subnet} ] 不是一个合规的网络！\n{e}"

        # 记录子网信息
        subnet_info['cidr'] = network.with_prefixlen
        subnet_info['version'] = network.version
        subnet_info['network_address'] = network.network_address
        subnet_info['broadcast_address'] = network.broadcast_address
        subnet_info['netmask'] = network.netmask
        subnet_info['hostmask'] = network.hostmask
        if network.prefixlen == (network.max_prefixlen - 1):
            subnet_info['first_address'] = network.network_address
            subnet_info['last_address'] = network.broadcast_address
            subnet_info['num_addresses'] = 2
            subnet_info['host_addresses'] = 2
        elif network.prefixlen == network.max_prefixlen:
            subnet_info['first_address'] = network.network_address
            subnet_info['last_address'] = network.network_address
            subnet_info['num_addresses'] = 1
            subnet_info['host_addresses'] = 1
        else:
            subnet_info['first_address'] = network[1]
            subnet_info['last_address'] = network[-2]
            subnet_info['num_addresses'] = network.num_addresses
            subnet_info['host_addresses'] = network.num_addresses - 2
        return subnet_info

    # 获取多个子网信息
    def get_multiple_subnet_info(self, subnets):
        subnets_info = []
        for subnet in subnets:
            subnet_info = self.get_single_subnet_info(subnet)
            brief_info = (
                subnet_info["cidr"], subnet_info["netmask"], subnet_info["first_address"], subnet_info["last_address"],
                subnet_info["broadcast_address"])
            subnets_info.append(brief_info)
        return subnets_info

    # 指定子网掩码
    def calculate_subnets_by_new_prefix(self, network, new_prefixlen):
        if new_prefixlen < network.prefixlen or network.max_prefixlen < new_prefixlen:
            return []
        return list(network.subnets(new_prefix=new_prefixlen))

    # 指定地址数量
    def calculate_subnets_by_num_address(self, network, num_address):
        if network.num_addresses < num_address:
            return []
        host_prefixlen = ceil(log2(num_address))
        new_prefixlen = network.max_prefixlen - host_prefixlen
        return self.calculate_subnets_by_new_prefix(network=network, new_prefixlen=new_prefixlen)

    # 指定子网数量
    def calculate_subnets_by_num_subnets(self, network, num_subnets):
        if network.num_addresses < num_subnets:
            return []
        new_num_address = int(network.num_addresses / num_subnets)
        return self.calculate_subnets_by_num_address(network=network, num_address=new_num_address)

    # 子网汇总聚合
    def aggregation_subnets_by_new_prefix(self, subnets, new_prefixlen):
        valid_supernets = []
        invalid_subnets = set()
        for subnet in subnets:
            try:
                subnet = ip_network(subnet, strict=False)
                if subnet.max_prefixlen < new_prefixlen:
                    print("指定的掩码超出范围")
                    # continue
                if subnet.prefixlen <= new_prefixlen:
                    valid_supernets.append(subnet)
                    continue
                supernet = subnet.supernet(new_prefix=new_prefixlen)
                valid_supernets.append(supernet)
            except ValueError:
                invalid_subnets.add(subnet)
        aggregated_subnets = list(collapse_addresses(valid_supernets))
        aggregated_subnets.sort()
        return aggregated_subnets, list(invalid_subnets)

    # 在Text组件输出信息
    def show_info_in_text_weight(self, info, text_weight):
        text_weight.config(state='normal')
        text_weight.delete('1.0', END)
        if isinstance(info, dict):
            text_weight.insert(END, self.format_network_info(info))
        elif isinstance(info, list):
            for line in info:
                text_weight.insert(END, f"{line}\n")
        else:
            messagebox.showerror("错误", info)
        text_weight.config(state='disabled')

    # 在Tree组件输出信息
    def show_info_in_tree_weight(self, info, tree_weight):
        for item in tree_weight.get_children():
            tree_weight.delete(item)
        if isinstance(info, list):
            for item in info:
                tree_weight.insert("", "end", values=item)
        else:
            messagebox.showerror("错误", info)

    # 从Entry组件读取整数
    def read_intger_from_entry_weight(self, entry_weight):
        try:
            value = int(entry_weight.get())
            return value
        except TypeError:
            return None
        except ValueError:
            return None

    # 从Entry组件读取非空值
    def read_non_empty_value_from_entry_weight(self, entry_weight):
        entry_value = entry_weight.get()
        if entry_value:
            return entry_value
        else:
            return None

    # 从Text组件读取非空行内容
    def read_non_empty_lines_from_text_weight(self, text_weight):
        text_lines = text_weight.get("1.0", END).splitlines()
        non_empty_lines = [line for line in text_lines if line.strip()]
        return non_empty_lines

    # 强制让组件获得焦点
    def force_weight_to_focus(self, weight):
        weight.focus_force()


class Event(Utils):
    def __init__(self):
        pass

    # =================== 事件1——子网信息 =================== #
    # 触发点击按钮
    def on_click_get_info_btn(self, *args):
        address = self.address_entry.get()
        mask = self.mask_entry.get()
        if not address:
            messagebox.showwarning("警告", "未填写网络地址！")
            self.force_weight_to_focus(weight=self.address_entry)
        elif not mask:
            messagebox.showwarning("警告", "未填写子网掩码！")
            self.force_weight_to_focus(weight=self.mask_entry)
        else:
            info = self.get_single_subnet_info(f"{address}/{mask}")
            self.show_info_in_text_weight(info, self.detail_info)

    # =================== 事件2——子网划分 =================== #
    # 触发变更划分方式
    def on_change_division_method(self, *args):
        selected_item = self.method_combobox.get()
        if selected_item == "1. 指定新子网的子网掩码":
            self.method_label.config(text='子网掩码:')
        elif selected_item == "2. 指定新子网的子网数量":
            self.method_label.config(text='子网数量:')
        else:
            self.method_label.config(text='地址数量:')

    # 触发划分子网功能
    def on_click_division_btn(self, *args):
        # 解析网络信息
        try:
            new_subnet = None
            address = str(self.prepare_address_entry.get())
            mask = str(self.current_mask_entry.get())
            method = self.method_combobox.get()
            new_subnet = int(self.new_subnets_entry.get())

            network = ip_network(f"{address}/{mask}", strict=False)
            # 按需求划分出所有子网
            if method == "1. 指定新子网的子网掩码":
                new_subnets = self.calculate_subnets_by_new_prefix(
                    network, new_subnet)
            elif method == "2. 指定新子网的子网数量":
                new_subnets = self.calculate_subnets_by_num_subnets(
                    network, new_subnet)
            else:
                new_subnets = self.calculate_subnets_by_num_address(
                    network, new_subnet)
            # 判断计算结果是否为空
            if new_subnets == []:
                messagebox.showwarning(
                    "警告", f"{self.method_label.cget('text')} 超出最大范围！")
                self.force_weight_to_focus(weight=self.new_subnets_entry)
            # 获取所有子网信息
            subnets_info = self.get_multiple_subnet_info(new_subnets)
            # 显示子网信息
            self.show_info_in_tree_weight(
                info=subnets_info, tree_weight=self.subnet_info_tree)

        except ValueError as e:
            if not address:
                messagebox.showwarning("警告", "未填写网络地址！")
                self.force_weight_to_focus(weight=self.prepare_address_entry)
            elif not mask:
                messagebox.showwarning("警告", "未填写子网掩码！")
                self.force_weight_to_focus(weight=self.current_mask_entry)
            elif new_subnet is None:
                messagebox.showwarning("警告", "未填有效值！")
                self.force_weight_to_focus(weight=self.new_subnets_entry)
            else:
                self.show_info_in_tree_weight(
                    info=f" {address}/{mask} 不合规的网络！\n{e}", tree_weight=self.subnet_info_tree)

    # 触发导出子网信息
    def on_click_export_btn(self, *args):
        # 选择文件保存路径
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")])
        if file_path:
            try:
                # 写入文件
                with open(file_path, mode='w', newline='\n', encoding='utf-8') as f:
                    csv_writer = writer(f)
                    columns = [self.subnet_info_tree.heading(
                        column)['text'] for column in self.subnet_info_tree['columns']]
                    csv_writer.writerow(columns)
                    for row_id in self.subnet_info_tree.get_children():
                        values = self.subnet_info_tree.item(row_id)['values']
                        csv_writer.writerow(values)
                messagebox.showinfo("导出成功", f"成功将子网信息导出到 {file_path} ！")
            except PermissionError:
                messagebox.showwarning(
                    "文件被占用", " CSV 文件被其他程序占用！请先关闭 CSV 文件后重试！")
        else:
            messagebox.showwarning("告警", "未选择保存文件路径！")

    # =================== 事件3——子网汇总 =================== #
    # 触发汇总子网功能
    def on_click_aggregate_subnet_btn(self, *args):
        pending_subnets = self.read_non_empty_lines_from_text_weight(
            text_weight=self.pending_text)
        new_prefixlen = self.read_intger_from_entry_weight(
            entry_weight=self.expect_mask_entry)
        if pending_subnets == []:
            messagebox.showwarning("告警", f"未填写有效子网：{pending_subnets}")
            self.force_weight_to_focus(weight=self.pending_text)
        elif new_prefixlen == None or new_prefixlen < 1:
            messagebox.showwarning("告警", f"未填写有效子网掩码：{new_prefixlen}")
            self.force_weight_to_focus(weight=self.expect_mask_entry)
        else:
            aggregated_subnets, invalid_subnets = self.aggregation_subnets_by_new_prefix(
                subnets=pending_subnets, new_prefixlen=new_prefixlen)
            self.show_info_in_text_weight(
                info=aggregated_subnets, text_weight=self.success_text)
            self.show_info_in_text_weight(
                info=invalid_subnets, text_weight=self.failed_text)

    # 触发清除信息功能
    def on_click_clear_info_btn(self):
        self.pending_text.config(state='normal')
        self.pending_text.delete('1.0', END)

        self.success_text.config(state='normal')
        self.success_text.delete('1.0', END)
        self.success_text.config(state='disabled')

        self.failed_text.config(state='normal')
        self.failed_text.delete('1.0', END)
        self.failed_text.config(state='disabled')

    # 触发导出结果功能
    def on_click_export_result_btn(self):
        # 选择文件保存路径
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")])
        if file_path:
            try:
                aggregate_success_lines = self.read_non_empty_lines_from_text_weight(
                    text_weight=self.success_text)
                aggregate_failed_lines = self.read_non_empty_lines_from_text_weight(
                    text_weight=self.failed_text)
                # 确定行数，以行数多的为准
                max_lines = max(len(aggregate_success_lines),
                                len(aggregate_failed_lines))
                with open(file_path, mode='w', newline='', encoding='utf-8') as f:
                    csv_writer = writer(f)
                    # 写入表头
                    csv_writer.writerow(['汇总完成', '汇总失败'])
                    for i in range(max_lines):
                        one_line_of_success = aggregate_success_lines[i] if i < len(
                            aggregate_success_lines) else ''
                        one_line_of_failed = aggregate_failed_lines[i] if i < len(
                            aggregate_failed_lines) else ''
                        csv_writer.writerow(
                            [one_line_of_success, one_line_of_failed])

                messagebox.showinfo("导出成功", f"成功将汇总结果导出到 {file_path} ！")
            except PermissionError:
                messagebox.showwarning(
                    "文件被占用", " CSV 文件被其他程序占用！请先关闭 CSV 文件后重试！")
        else:
            messagebox.showwarning("告警", "未选择保存文件路径！")


class Page(Event):
    def __init__(self, root):
        # 初始化主窗口属性
        self.root = root
        self.root.title("Simple CIDR Tool")
        window_width = 800
        window_height = 800
        self.font_style = ('Microsoft YaHei UI', 10)
        # 获取当前显示器尺寸信息
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        # 设置程序主窗口弹出位置（水平居中）
        x = (screen_width / 2) - (window_width / 2)
        y = (screen_height / 2) - (window_height / 2)
        self.root.geometry(f'{window_width}x{window_height}+{int(x)}+{int(y)}')
        # 绘制窗口
        self.draw_main_window_layout(self.root)

    # 绘制主窗口框架布局
    def draw_main_window_layout(self, root):
        # 创建选项卡
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)
        # 创建Frame
        self.info_frame = ttk.Frame(self.notebook)
        self.division_frame = ttk.Frame(self.notebook)
        self.aggregation_frame = ttk.Frame(self.notebook)
        # 将Frame添加至选项卡
        self.notebook.add(self.info_frame, text='子网信息')
        self.notebook.add(self.division_frame, text='子网划分')
        self.notebook.add(self.aggregation_frame, text='子网汇总')
        # 分别在三个选项卡下初始化页面
        self.draw_subnet_info_page(self.info_frame)
        self.draw_subnet_division_page(self.division_frame)
        self.draw_subnet_aggregation_page(self.aggregation_frame)

    # =================== 页面1——子网信息 =================== #
    # 绘制子网信息页面
    def draw_subnet_info_page(self, tab_frame):
        # 第一行：基本信息 LabelFrame
        basic_info_frame = self.create_LabelFrame_with_pack(
            frame=tab_frame, text="基本信息")

        ttk.Label(basic_info_frame, text="网络地址:", font=self.font_style).grid(
            row=0, column=0, padx=5, sticky='e')
        self.address_entry = self.create_Entry_with_grid(
            frame=basic_info_frame, event=self.on_click_get_info_btn, row=0, column=1)
        self.address_entry.focus_force()

        ttk.Label(basic_info_frame, text="子网掩码:", font=self.font_style).grid(
            row=0, column=2, padx=5, sticky='e')
        self.mask_entry = self.create_Entry_with_grid(
            frame=basic_info_frame, event=self.on_click_get_info_btn, row=0, column=3)

        self.get_info_btn = ttk.Button(
            basic_info_frame, text="获取信息", command=self.on_click_get_info_btn).grid(row=0, column=4, padx=5)

        # 第二行：详细信息 LabelFrame
        detail_info_frame = self.create_LabelFrame_with_pack(
            frame=tab_frame, text="详细信息", expand=True)
        self.detail_info = Text(detail_info_frame, height=18, state='disabled',
                                font=self.font_style, spacing1=4, spacing3=4, relief="flat", padx=10, pady=5)
        self.detail_info.pack(expand=True, fill='both')

    # =================== 页面2——子网划分 =================== #
    # 绘制子网划分页面
    def draw_subnet_division_page(self, tab_frame):
        # 第1行：待规划网络信息 LabelFrame
        info_frame = self.create_LabelFrame_with_pack(
            frame=tab_frame, text="待规划网络信息")

        ttk.Label(info_frame, text="网络地址:", font=self.font_style).grid(
            row=0, column=0, padx=5, sticky='e')
        self.prepare_address_entry = self.create_Entry_with_grid(
            frame=info_frame, event=self.on_click_division_btn, row=0, column=1)
        self.prepare_address_entry.focus_force()

        mask_label = ttk.Label(info_frame, text="子网掩码:", font=self.font_style).grid(
            row=0, column=2, padx=5, sticky='e')
        self.current_mask_entry = self.create_Entry_with_grid(
            frame=info_frame, event=self.on_click_division_btn, row=0, column=3)

        # 第2行：子网规划方式 LabelFrame
        method_frame = self.create_LabelFrame_with_pack(
            frame=tab_frame, text="子网规划方式")

        self.method_combobox_var = StringVar()
        ttk.Label(method_frame, text="规划方式:", font=self.font_style).grid(
            row=0, column=0, padx=5, sticky='e')
        self.method_combobox = ttk.Combobox(method_frame, textvariable=self.method_combobox_var, values=[
                                            "1. 指定新子网的子网掩码", "2. 指定新子网的子网数量", "3. 指定新子网的地址数量"])
        self.method_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.method_combobox.current(0)
        self.method_combobox_var.trace('w', self.on_change_division_method)

        self.method_label = ttk.Label(
            method_frame, text="子网掩码:", font=self.font_style)
        self.method_label.grid(row=0, column=2, padx=5, sticky='e')
        self.new_subnets_entry = self.create_Entry_with_grid(
            frame=method_frame, event=self.on_click_division_btn, width=5, row=0, column=3)

        ttk.Button(method_frame, text="划分子网", command=self.on_click_division_btn).grid(
            row=0, column=4, padx=5)
        ttk.Button(method_frame, text="导出信息", command=self.on_click_export_btn).grid(
            row=0, column=5, padx=5)

        # 第3行：详细信息 LabelFrame
        subnets_info_frame = self.create_LabelFrame_with_pack(
            frame=tab_frame, text="规划完成的子网信息", expand=True)
        # show="headings" 隐藏Treeview的`#0`列
        self.subnet_info_tree = ttk.Treeview(subnets_info_frame, columns=(
            'network', 'netmask', 'first', 'last', 'broadcast'), show="headings", height=18)
        self.subnet_info_tree.heading('network', text='子网')
        self.subnet_info_tree.heading('netmask', text='子网掩码')
        self.subnet_info_tree.heading('first', text='首个可用地址')
        self.subnet_info_tree.heading('last', text='最后可用地址')
        self.subnet_info_tree.heading('broadcast', text='广播地址')
        self.subnet_info_tree.column('network', width=150, anchor=CENTER)
        self.subnet_info_tree.column('netmask', width=150, anchor=CENTER)
        self.subnet_info_tree.column('first', width=100, anchor=CENTER)
        self.subnet_info_tree.column('last', width=100, anchor=CENTER)
        self.subnet_info_tree.column('broadcast', width=100, anchor=CENTER)
        self.subnet_info_tree.pack(expand=True, fill='both')

    # =================== 页面3——子网汇总 =================== #
    # 绘制子网汇总页面
    def draw_subnet_aggregation_page(self, tab_frame):
        # 外层上下两个 Frame
        outer_frame = self.create_Frame_with_pack(frame=tab_frame)
        outer_frame.rowconfigure(0, weight=9)
        outer_frame.rowconfigure(1, weight=1)
        outer_frame.columnconfigure(0, weight=1)

        upper_frame = self.create_Frame_with_grid(
            frame=outer_frame, row=0, column=0)
        lower_frame = self.create_Frame_with_grid(
            frame=outer_frame, row=1, column=0)

        # 上面的 Frame 分为左右两列
        upper_frame.columnconfigure(0, weight=1)
        upper_frame.columnconfigure(1, weight=1)
        upper_frame.rowconfigure(0, weight=1)

        upper_left_frame = self.create_Frame_with_grid(
            frame=upper_frame, row=0, column=0)

        # 上面左列的 Frame 内容
        # 等待汇总子网列表
        pending_list_frame = self.create_LabelFrame_with_grid(
            frame=upper_left_frame, text="等待汇总子网列表", row=0, column=0, sticky="nsew", row_weight=1, column_weight=1)
        upper_left_frame.rowconfigure(0, weight=1)
        upper_left_frame.columnconfigure(0, weight=1)
        self.pending_text = self.create_Text_with_pack(
            frame=pending_list_frame, state='normal')

        # 上面右列的 Frame 内容
        # 汇总完成和汇总失败的 LabelFrame
        upper_right_frame = self.create_Frame_with_grid(
            frame=upper_frame, row=0, column=1)
        upper_right_frame.rowconfigure(0, weight=3)
        upper_right_frame.rowconfigure(1, weight=7)
        upper_right_frame.columnconfigure(0, weight=1)

        success_frame = self.create_LabelFrame_with_grid(
            frame=upper_right_frame, text="汇总完成", row=0, column=0)
        self.success_text = self.create_Text_with_pack(
            frame=success_frame, state='disabled')

        failed_frame = self.create_LabelFrame_with_grid(
            frame=upper_right_frame, text="汇总失败", row=1, column=0)
        self.failed_text = self.create_Text_with_pack(
            frame=failed_frame, state='disabled')

        # 下面的 Frame 内容
        button_frame = ttk.Frame(lower_frame)
        button_frame.pack(anchor=CENTER)

        # 期望汇总后的子网掩码
        expect_mask_label = ttk.Label(button_frame, text="期望汇总后的子网掩码")
        expect_mask_label.pack(side=LEFT, padx=5, pady=10)

        self.expect_mask_entry = ttk.Entry(button_frame, width=5)
        self.expect_mask_entry.pack(
            side=LEFT, padx=5, pady=10, expand=True, fill='both')
        self.expect_mask_entry.bind(
            '<Return>', self.on_click_aggregate_subnet_btn)

        # 汇总子网按钮
        aggregate_button = self.create_Button_with_pack(
            frame=button_frame, text="汇总子网", command=self.on_click_aggregate_subnet_btn)
        # 清除信息按钮
        clear_button = self.create_Button_with_pack(
            frame=button_frame, text="清除信息", command=self.on_click_clear_info_btn)
        # 导出结果按钮
        export_button = self.create_Button_with_pack(
            frame=button_frame, text="导出结果", command=self.on_click_export_result_btn)

    def create_Frame_with_pack(self, frame, expand=True, fill='both', padx=10, pady=10):
        new_frame_weight = ttk.Frame(frame)
        new_frame_weight.pack(expand=expand, fill=fill, padx=padx, pady=pady)
        return new_frame_weight

    def create_Frame_with_grid(self, frame, row=0, column=0, sticky="nsew"):
        new_frame_weight = ttk.Frame(frame)
        new_frame_weight.grid(row=row, column=column, sticky=sticky)
        return new_frame_weight

    def create_Entry_with_grid(self, frame, event, row, column, width=20, padx=5):
        new_entry_weight = ttk.Entry(frame, width=width, font=self.font_style)
        new_entry_weight.grid(row=row, column=column, padx=padx)
        new_entry_weight.bind('<Return>', event)
        return new_entry_weight

    def create_Text_with_pack(self, frame, state='normal', relief="flat", padx=10, pady=5, expand=True, fill='both'):
        new_text_weight = Text(
            frame, state=state, relief=relief, padx=padx, pady=pady)
        new_text_weight.pack(expand=expand, fill=fill)
        return new_text_weight

    def create_LabelFrame_with_pack(self, frame, text, padding=10, borderwidth=2, relief="flat", padx=10, pady=10, fill='both', expand=False):
        new_labelframe_weight = ttk.LabelFrame(
            frame, text=text, padding=padding, borderwidth=borderwidth, relief=relief)
        new_labelframe_weight.pack(
            padx=padx, pady=pady, fill=fill, expand=expand)
        return new_labelframe_weight

    def create_LabelFrame_with_grid(self, frame, text, padding=10, borderwidth=2, relief="flat", row=0, column=0, sticky="nsew", row_weight=1, column_weight=1):
        new_labelframe_weight = ttk.LabelFrame(
            frame, text=text, padding=padding, borderwidth=borderwidth, relief=relief)
        new_labelframe_weight.grid(row=row, column=column, sticky=sticky)
        new_labelframe_weight.rowconfigure(0, weight=row_weight)
        new_labelframe_weight.columnconfigure(0, weight=column_weight)
        return new_labelframe_weight

    def create_Button_with_pack(self, frame, text, command, side=LEFT, padx=20, pady=10):
        return ttk.Button(frame, text=text, command=command).pack(side=LEFT, padx=20, pady=10)


if __name__ == '__main__':
    root = Tk()
    app = Page(root)
    root.mainloop()
