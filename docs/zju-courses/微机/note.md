# 微机原理及其应用

分为理论课和实验课，主要学习的是 8051 单片机。

记录一些上课笔记，内容大部分和课件重合因为主要是防止上课会睡过去，然后增加一些辅助理解的东西。

!!! info "成绩构成"


## 1. 绪论

mcs 51

**存储器**：
字节
![500](assets/note.png)

高四位：D7,D6,D5,D4  
低四位：D3,D2,D1,D0

后续出现指令：SWAP 即交换高四位和低四位


**数制**

![500](assets/note-1.png)

数制转换  
整数：  
- 除 2 取余法
- 分解权之和法
小数：  
	乘 2 取整，限定精度
	![350](assets/note-2.png)

二进制转十六进制。不足四位的补 0
![350](assets/note-3.png)


**数的表示方式**

1. 原码
	![400](assets/note-4.png)
2. 反码
	主要是负数有例外
	$$
	[正数]_反​=[正数]_原​ 
	$$$$
	[负数]_反​=[对应正数]_原​取反​
	$$
	![400](assets/note-5.png)
3. 补码：计算机中用补码表示
	![400](assets/note-6.png)


字符表示：

-9➡️11110111 B➡️F7 H

!!! note "作业"
	![500](assets/homework.png)


## 2. MCS-51单片机结构

### 内部结构与外部引脚
**内部结构**  

1. 中央处理器 CPU：8 位，运算器+控制器  
2. 内部数据存储器 RAM：128 字节，**存放可读写的数据**，RAM 里有很多地址  
3. 内部程序存储器 ROM：4 K，存放程序和常数  
4. 定时/计数器：2 个 16 位  
5. 并行 I/O 口：4 个 8 位 I/O 口，P0-P3，数据的并行输入输出  
6. 串行口：一个全双工的串行口,实现单片机和其他数据设备之间的串行数据传送  
7. 中断控制系统：5个中断源:2个外部中断,2个定时/计数中断,1个串行中断  
8. 时钟电路  
9. 总线  

![500](assets/note-7.png)


**外部引脚**
![500](assets/note-8.png)

![500](assets/note-9.png)

P3 口是分散的

控制线：
ALE：区分地址信号
PSEN：控制ROM

### 8051内部存储器

**内部数据存储器 RAM**

![500](assets/note-10.png)

1. **寄存器区：00H - 1FH**
	有四组寄存器区，如上图，每组都有 `R0 R1 R2 R3 R4 R5 R6 R7` 对应 RAM 中的地址，如第 0 组，R0➡️00H
	
2. **位寻址区：20H-2FH**  
	![500](assets/note-12.png)
3. **用户 RAM 区**  
	![352](assets/note-11.png)
4. **特殊功能寄存区 80H-FFH**  
	符号和名称要记，地址不用记
	![](assets/note-13.png)
	
	**PC**：程序计数器   
		16 位计数器，存放将要执行的指令的地址  
		![](assets/note-14.png)
	**ACC**：累加器， 8 位专用寄存器
		按寻址方式分为：
		A-寄存器方式
		ACC-直接地址方式
	**B**：B 寄存器，8 位寄存器，主要用于乘除运算指令
	**PSW**：程序状态字
		![](assets/note-15.png)
		> RS1 和 RS0 控制选择的寄存器区是哪一组
	**DPTR**：数据指针 `Data Pointer` ，指针是存放地址的变量
		![](assets/note-16.png)
	**SP**：堆栈指针 `Stack Pointer`：保存栈顶地址
		>  SP 本身也是一个寄存器，里面放的是一个 RAM 地址
		

!!! note "堆栈"
	堆栈是按照“先进后出、后进先出”原则进行存取的内存区域。存 abc 取 cba  
	进栈：先 SP + 1，再写数据  
	**例**：SP = 40H；A = 35H，把 A 保存到栈顶
	PUSH ACC 
	SP = SP + 1;SP = 41H
	RAM[41H] = 35H

POP：SP - 1 然后读数据

堆栈的作用：  
1. 临时保存数据
2. 保存程序返回地址，保护程序断点和数据


**内部程序存储器 ROM**

通过 pc 指针读取指令代码

>  程序储存在 ROM 中，PC 是程序计数器 Program Counter 用来保存**将要执行的指令地址**，而且有自动加 1 的功能


![400](assets/note-17.png)


R0、R1 可以作为普通的数据寄存器，也可以作为地址指针，通过@Ri 进行间接寻址  
比如：
```
MOV R0,#30H
MOV A,@R0
```

!!! note "指针"
	指针是一个里面保存“地址”的东西。



### 单片机并行 I/O 口
4 个 8 位并行口:P0,P1,P2,P3, 具有字节寻址和位寻址的功能。  
4 个端口在结构上相同之处: P0 -- P3 都是**准双向** I/0 口，作输入时，必须先向相应端口的锁存器写人 “1”。   
4 个端口在结构上不同之处: P0 口无内部上拉电阻，不能提供拉电流输出， 而 P1--P3 则带内部上拉电阻，可以提供拉电流输出。当 P0 口作通用 I/0 口输出使用时，需外接上拉电阻才可输出高电平。

![200](assets/note-18.png)![200](assets/note-20.png)![200](assets/note-21.png) ![200](assets/note-19.png)

![](assets/note-22.png)


### 时钟与定时

时钟电路：  
- 震荡电路
- 分频电路
- 晶振频率
- 外部引入脉冲信号驱动的时钟电路

CPU 时序
![](assets/note-23.png)


### 复位电路


1. 功能：复位启动单片机。 
2. 复位条件：在 RST 引脚输入 2 个机器周期以上的高电平。正常工作时保持为低电平。
3. 复位电路
	![330](assets/note-24.png)
4. 复位操作
	![](assets/note-25.png)






## 3. MCS-51 指令系统

![](assets/note-26.png)

标号，操作码，操作数，注释

### 寻址方式

**寻址方式**：寻找操作数地址的方法。操作数的表示方法（CPU 如何找到操作的数据？）

分类还有一些例子

1. 立即寻址：操作数在指令中  
	指令： 
	`MOV A,#20H`
	`MOV DPTR,#1234H`
2. 直接寻址：内部RAM地址在指令中（直接写地址)  
	指令：`MOV A,30H ` ➡️ `A = RAM[30H]`
3. 寄存器寻址：操作数在寄存器中（写的是寄存器，比如 R0、R1）  
	指令：`MOV RO,#10H` `MOV A,R0` ➡️ `A = 10H`
4. 寄存器间接寻址：操作数地址在寄存器中
	指令：`MOV A,@R0` 假如 `R0 = 30H,RAM[30H] = 66H` 则 `A = 66H`
5. 变址寻址：操作数地址在基址寄存器和变址寄存器中，访问 ROM 中的数据
	指令：`MOVC A,@A+DPTR` , `MOVC A,@A+PC`
	例：`DPTR = 2000H ; A = 05H`  `MOVC A,@A+DPTR` ➡️ `A = ROM[2005H]`
6. 相对寻址：转移地址（目的地址）的相对偏移量在指令中，主要用于跳转 
	指令： `JC NEXT`
7. 位寻址：位地址在指令中，操作一个 bit
	指令 `MOV C,PSW.5`

### 指令系统

符号约定

![](assets/note-27.png)

**数据传送指令**

1. 以 A 为目的的操作数  
	`MOV A,Rn` 
	`MOV A,direct` 
	`MOV A,@Ri` 
	`MOV A,#data`
2. 以 Rn 为目的的操作数  
	`MOV Rn,A` 
	`MOV Rn,direct` 
	`MOV Rn,#data`
3. 以直接地址为目的的操作数
	`MOV direct,A` 
	`MOV direct,Rn`
	`MOV direct1,direct2` 
	`MOV direct,@Ri` 
	`MOV direct,#data` 
4. 以寄存器间接地址为目的的操作数
	`MOV @Ri,A`
	`MOV @Ri, direct`
	`MOV @Ri,#data` 
5. 16 位数传送
	`MOV DPTR,#data16` eg `MOV DPTR,#1234H`
6. 外部 RAM 数据传送
	读取指令：`MOVX A,@DPTR` `MOVX A,@Ri`
	写指令：`MOVX @DPTR,A` `MOVX @Ri,A`
7. 程序存储器数据传送
	`MOVX A,@A+PC` `MOVX A,@A+DPTR`
8. 数据交换指令
	![364](assets/note-30.png)
9. 堆栈操作指令组  
	进栈：PUSH direct  
	出栈： POP direct  

例题：

![](assets/note-28.png)

1.  `MOV A,R7` `MOV R6,A`  
>  注：不能直接写 `MOV R6,R7`，8051 不支持两个工作寄存器之间直接传送，所以要通过累加器 A 中转
	$$
	R7 \rightarrow A \rightarrow R6
	$$
2.  `MOV A,20H` `MOV DPTR,#0020H` `MOVX @DPTR,A`   
> 注：DPTR 通常在访问外部存储器时使用，用于存放地址数据，先把内部 RAM `20H` 的内容读入 A，再用 `MOVX` 写入外部 RAM
	$$
	内部RAM[20H]\rightarrow A\rightarrow 外部RAM[0020H]
	$$
3. `MOV DPTR,#0020H` `MOV A,#00H` `MOVC A,@A+DPTR` `MOV 20H,A`  
	$$
	程序ROM[20H]\rightarrow A\rightarrow 内部RAM[20H]
	$$
4. `MOV A,20H` `SWAP A` `MOV 20H,A`   
>  注：SWAP 只能操作累加器 A，所以要先把 20H 取到 A
	
5. `MOV A,20H` `XCH A,30H` `MOV 20,A`  
>  数据交换可以使用 XCH 指令

**算数运算指令**

1. 加法指令  
		- 不带进位位加法：`ADD A,#data(direct,Rn,@Ri)`  
		- 带进位位加法：`ADDC A,#data(direct,Rn,@Ri)`  
		- 加 1 指令：`INC A(Rn,direct,@Ri,DPTR)`
		- 十进制调整：`DA A`
2. 减法指令
	1. `SUBB A,Rn(direct,@Ri,#data)`
	2. `DEC A(Rn,direct,@Ri)` 减 1 指令
		>  注意，SUBB 指令 A=A-操作数-Cy（PSW 程序状态字里的第一位，即进位标志位）
3. 乘法指令：`MUL AB` ➡️A * B 结果：B 为高八位，A 为低 8 位
> 例：
> 
4. 除法指令：`DIV AB`，A/B结果：A 为商，B 为余数

**逻辑运算指令、移位指令**

1. 与指令：`ANL A，Rn`  
	>  写出二进制进行与计算，有 0 则 0
2. 或指令：`ORL A，Rn`  
	>  有 1 则 1
3. 异或指令：`XPL A，Rn`  
	>  相同为 0，不同为 1，偶数次异或不变
4. 累加器清零和取反：`CLR A`；`CPL A`  
5. 左移指令  
	![](assets/note-43.png)
6. 右移指令  
	![](assets/note-44.png)


**控制转移指令**

1) 无条件转移指令
	![](assets/note-46.png)
2) 条件转移指令
	![](assets/note-47.png)
	![](assets/note-48.png)
3) 子程序 `ACALL`；`LCALL`
	![](assets/note-49.png)
4) 空指令 `NOP`


**位操作指令**

![](assets/note-45.png)


**伪指令**
>  告诉汇编程序汇编方法的命令，不生成机器代码。

汇编起始地址

	

**数据传送指令**



![](assets/note-29.png)



![](assets/note-50.png)

> 这里的 5.2 要好好考虑一下


## 4. 汇编语言程序设计

### 4.1 顺序程序设计

!!! note "例题"
	3 字节无符号数相加，其中被加数在内部 RAM 的 50H、51H 和 52H 单元中；加数在内部 RAM 的 53H、54H 和 55H 单元中；要求把相加之和存放在 50H、51H 和 52H 单元中，进位存放在位寻址区的 20H 位中。

![](assets/note-31.png)

```

ORG 0000H

MOV R0,#52H \\存放地址
MOV R1,#55H

; 第一步：最低字节相加
MOV A,@R0  \\寄存器间接寻址
ADD A,@R1
MOV @R0,A

DEC R0
DEC R1

; 第二步：中间字节相加
MOV A,@R0
ADDC A,@R1
MOV @R0,A

DEC R0
DEC R1

; 第三步：最高字节相加
MOV A,@R0
ADDC A,@R1
MOV @R0,A

; 第四步：保存最终进位
CLR A
ADDC A,#00H
MOV R0,#20H
MOV @R0,A

SJMP $
END

```



>  三字节数 123456H  
>  加法运算要用累加器 A，A 是八位累加器，进位会放到 Cy 位中
>  ADD 是不带进位的加法，ADDC 是带进位的加法
>  `STMP $` 如果没有这个指令，cpu 会读取 rom 中程序单元之外的代码，不会停下来




### 4.2 分支程序设计
- 采用条件转移指令：
- 二分支

!!! note "例题"
	假定在外部 RAM 中有 ST1、ST2 和 ST3 共 3 个连续单元，其中 ST1 和 ST2 单元中存放着两个无符号二进制数，要求找出其中的大数并存入 ST3 单元中。

![](assets/note-32.png)

```

START:
    CLR C
    MOV DPTR,#ST1
    MOVX A,@DPTR
    MOV R2,A

    INC DPTR
    MOVX A,@DPTR

    SUBB A,R2
    JNC BIG1

    XCH A,R2

BIG0:
    INC DPTR
    MOVX @DPTR,A
    RET

BIG1:
    MOVX A,@DPTR
    SJMP BIG0

```

>  用 SUBB 判断正负的原理其实是看 cy 位，会不会借位


**多分支程序设计**

![](assets/note-33.png)

>  不能用 SUBB，因为不需要借位， cy 位始终为 0


先画流程图再编写程序
![306](assets/note-34.png)

程序：
![313](assets/note-35.png)


### 4.3 循环程序设计

![](assets/note-36.png)


!!! note "例题"
	![](assets/note-37.png)



### 4.4 子程序设计



![282](assets/note-38.png)


![390](assets/note-39.png)

>  为什么能延时
>  $机械周期 T_机=12 震荡周期=2*10^{-6}$
>  

![](assets/note-40.png)

### 4.5 查表程序设计

![](assets/note-41.png)

![](assets/note-42.png)