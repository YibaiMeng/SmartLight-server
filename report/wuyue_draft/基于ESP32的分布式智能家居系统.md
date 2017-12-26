## 基于ESP32的分布式智能家居系统——智能台灯

### ESP32简介

ESP32是一款WiFi和蓝牙系统级芯片（SoC），集成了完整的发射/接收射频功能。

ESP32带有2个32位、LX6 CPU,主频高达240MHz，采用7级流水线架构。

此芯片还带有丰富的外设，包括UART、SPI、I2C等通用的串行传输硬件单元，ADC和DAC，电容式触摸传感器、SDSDIO/MMC主控制器、PWM和RMT，以及EMAC以太网RMII接口控制器。

![](nodemcu_32s.png)

作为对比，STM32单片机高端F7系列的硬件性能为216MHz，512KB RAM，2M Flash，462 DMIPS，STM32F767IGT6的价格为75元左右，而240MHz双核，520KB SRAM，4M Flash，600DMIPS的ESP32邮票孔版本仅为26元，且自带WIFI蓝牙模块，性价比非常高。

项目采用ESP32开发板，价格为39元。

### 模块概述

为了合理利用ESP32的性能和外设，我们采用了FreeRTOS实时操作系统。与Linux系统不同的是，FreeRTOS近提供了任务调度和硬件控制的若干API，而并没有任务默认运行，没有Shell也没有各种Service，而这些都需要我们来实现。我们参考了若干例程，最终根据我们的需要实现了下面的功能：

1. 开机自动配置联网，由于我们的定位是智能家居，家庭里面的WIFI资源一般是固定的，不需要频繁改动
2. 配置联网后默认开启HTTP服务器（由我们自己实现的简单服务器）任务
3. 执行开机启动脚本，此脚本可以通过shell来更改，默认为空

图的表达为：

```mermaid
graph LR;
a[程序入口];
b[初始化WIFI];
c[初始化HTTP服务器]
d[执行开机启动脚本]
e[初始化并执行deamon1]
f[初始化并执行deamon2]
g[...]
h[接收HTTP请求]
i[请求静态文件]
j[请求运行脚本]
k[脚本解释执行器]
	a-->b
	b-->c
	b-->d
	d-->e
	d-->f
	d-->g
	c-->h
	h-->i
	h-->j
	j-->k
	i-->h
	k-->h
```

### 模块实现细节

#### HTTP服务器实现

使用嵌入汇编+Makefile的方式，避免了将html文本转为c字符串的操作：

```c
extern const char INDEX_HTML[] asm("_binary_index_html_start");
extern const char INDEX_HTML_END[] asm("_binary_index_html_end");
extern const char TEST_HTML[] asm("_binary_test_html_start");
extern const char TEST_HTML_END[] asm("_binary_test_html_end");
extern const char FAVICON_ICO[] asm("_binary_favicon_ico_start");
extern const char FAVICON_ICO_END[] asm("_binary_favicon_ico_end");

extern const char ERR_404_HTML[] asm("_binary_404_html_start");
extern const char ERR_404_HTML_END[] asm("_binary_404_html_end");
```

编写实现如下的HTTP函数。我们经过分析后认为HTTP协议本身作为包传输协议并不十分高效，而其好处就在于Header的信息是可读的，这方便了调试，更方便了扩展（非固定包头长度）。而它也有相应的局限性，最明显的地方就在于“客户-服务器”模型就确定了服务器不能主动发信息客户，而实际上在智能家居里面，传感器向我们发送信息是很常见的，对等的关系应该更贴切一些，于是我们实现了双向HTTP协议，两侧都可以向对方”问话“，而另一方则”尽可能马上回答“。在这样一个模型中，智能家居控制器可以像很多个”人”一样工作，随时都会有某个“人”告诉用户一些事情，用户也可以选择和某个“人”进行对话。

```c
struct DuHttp
{
    UINT8 type;
    char data[DUHTTP_DATASIZE];
    char* content;
    int contentLength;
    int headlineCount;
    struct {
    	char* key;
    	char* value;
	} headline[DUHTTP_MAXHEADLINECOUNT];
    union {
        struct {
			char requestedURL[128];
		} ask;
        struct {
    		int statusCode;
    		char reasonPhrase[32];
		} response;
    };
};
void DuHttp_Initialize(struct DuHttp* d);
void DuHttp_Initialize_GET(struct DuHttp* d, const char* requestedURL);
void DuHttp_Initialize_POST(struct DuHttp* d, const char* requestedURL);
void DuHttp_Initialize_RESPONSE(struct DuHttp* d, int statusCode, const char* reasonPhrase);
void DuHttp_Release(struct DuHttp* d);
char* DuHttp_FindValueByKey(struct DuHttp* d, const char* key);
void DuHttp_PushHeadline(struct DuHttp* d, const char* key, const char* value);
void DuHttp_PushData(struct DuHttp* d, const char* data, int dataLength);
void DuHttp_PushDataString(struct DuHttp* d, const char* str);
void DuHttp_EndHeadline(struct DuHttp* d);

struct DuHttpReceiver
{
#define DuHttpReceiver_State_RecevingHead 0
#define DuHttpReceiver_State_RecevingData 1
    int nowState;
    char headLineStr[DUHTTP_MAXLINESIZE];
    int headLineIndex;
    int hasReadDataLength;
    char queue[DUHTTPRECEIVER_BUFFERSIZE];
    int queue_write;
    int queue_read;
};

void DuHttpReceiver_Reset(struct DuHttpReceiver* r);
void DuHttpReceiver_Initialize(struct DuHttpReceiver* r);
char DuHttpReceiver_InBuf(struct DuHttpReceiver* r,
                          const char* buf, int bufsize);
char DuHttpReceiver_TryReadPack(struct DuHttpReceiver* r, struct DuHttp* pack);
void DuHttpReceiver_TryResolveHeadLine(const char* str, struct DuHttp* pack);
int DuHttpReceiver_AvailableSize(struct DuHttpReceiver* r);

int DuHttpSend(struct DuHttp* h, char* buf, int max_size);

char *url_decode(char *str);
```

同时对于网络的性能我们有一些优化，HTTP/1.0默认是每次进行传输结束后就关闭掉这个链接，我们调试阶段也同样是传输完成后就立即关闭，但通过少许改动就可以实现长连接传送多个包。

```c
DuHttp_PushHeadline(&sendDuHttp, "Connection", "keep-alive");
```

#### 运行程序模块

Shell本身不具备特殊的功能，而仅仅是把字符串转化成函数调用。当只有简单地几个函数的时候，简单地执行即可，然而我们希望实现一套可插件化拓展的功能，就不得不进行一些优雅的封装。

在Apache服务器中可以使用CGI程序来实现各种功能，而因为FreeRTOS没有一套动态执行程序的机制，我们实现了这个shell来支持有限的一些命令，并编写了驱动类（因为交叉编译器不支持C++，即使支持C++，在嵌入式系统中也尽量不用，会导致很多奇怪的问题），而对于c的函数式编程，又缺少封装而显得不优雅，于是我们将所有的
“类函数”描述成static的，并定义一个包含函数指针的struct，定义并初始化一个“驱动类”。

用WS2812全彩LED灯举例：

```c
typedef struct
{
	uint8_t g;
	uint8_t b;
	uint8_t r;
} wsRGB_t;

struct ws2812_t_struct {
	unsigned char initialized;
	rmt_channel_t channel;
	gpio_num_t gpio;
	rmt_item32_t* items;
	unsigned int size;
};
typedef struct ws2812_t_struct ws2812_t;
void WS2812B_initStruct(ws2812_t* w);

struct WS2812B_Module {
	void (*init)(struct ws2812_t_struct* self);
	void (*setLeds)(struct ws2812_t_struct* self, wsRGB_t* data, unsigned int size);
	void (*deInit)(struct ws2812_t_struct* self);
	struct {
		void (*task)(void* pvParameters);
		rmt_channel_t channel; // = 0
		gpio_num_t PIN; // = 18;
		unsigned int CNT; // = 16;
		int duration; // = 10; (second)
	} demo;
};
extern struct WS2812B_Module WS2812B;
```

通过非常简单的封装，我们让c语言也拥有了“类成员函数”，通过这样一种方式，驱动可以结构化地保存信息，在有很多个驱动的时候，我们添加一个驱动模块就是调用`WS2812B.init(&ws2812)`函数，非常地简洁。

同样地，借鉴了Linux下面的Daemon进程的观点，我们也编写了Daemon函数，来实现复杂的时序逻辑。下面是WS2812的标准Daemon：

```c
/* 这些函数是可以被别的Task调用的，异步和安全地改变LED的状态 */
extern int WS2812_daemon_SingleColor(wsRGB_t color, TickType_t delay);
extern int WS2812_daemon_Breathing(wsRGB_t color, TickType_t delay);
extern int WS2812_daemon_Rainbow(TickType_t delay);
extern int WS2812_daemon_Print(char* buf, size_t n);

/* 这些是daemon的执行函数 */
struct WS2812_state {
	TickType_t startTime;
	wsRGB_t pixels[pixel_count]; // using at
	int vec; // using as a bit set
	wsRGB_t para1;
	int para2;
	int para3;
	wsRGB_t para4;
	int type;
}; typedef struct WS2812_state WS2812_state_t;
static void initStat(WS2812_state_t* stat);

static WS2812_state_t* nowStat = NULL;
static WS2812_state_t* nextStat = NULL;

static int callUpdate(ws2812_t* ws2812, WS2812_state_t* stat, WS2812_state_t* nxtstat) {
	if (nxtstat == NULL || xTaskGetTickCount() < nxtstat->startTime) {
		// keep in this state
		if (stat->type == Type_SingleColor) {
			callSingleColor(ws2812, stat);
		} else if (stat->type == Type_Breathing) {
			callBreathing(ws2812, stat);
		} else if (stat->type == Type_Rainbow) {
			callRainbow(ws2812, stat);
		}
	} else { // change to next state
		initStat(stat); // avoid loop
		return 1;
	}
	return 0;
}

static const char TAG[] = "WS2812 daemon";

void WS2812_daemon_task(void *pvParameters) {
	ESP_LOGI(TAG, "Task started");

	ESP_LOGI(TAG, "Running Initialization step");
	ws2812_t ws2812;
	ws2812.channel = WS2812B.demo.channel; // rmt channel is 0
	ws2812.gpio = WS2812B.demo.PIN;
	ws2812.size = WS2812B.demo.CNT;
	WS2812B.init(&ws2812);
	const TickType_t delay = 30 / portTICK_PERIOD_MS; // 30ms
	nowStat = malloc(sizeof(WS2812_state_t));
	nextStat = malloc(sizeof(WS2812_state_t));
	if (nowStat == NULL || nextStat == NULL) {
		ESP_LOGE(TAG, "Malloc failed");
		goto errorDeinit;
	}
	nowStat->startTime = 0;
	nextStat->startTime = 0;

	ESP_LOGI(TAG, "daemon Initialization finished");

	while (1) {
		if (callUpdate(&ws2812, nowStat, nextStat)) { // swap
			WS2812_state_t* tmp = nowStat;
			nowStat = nextStat;
			nextStat = tmp;
		}
		vTaskDelay(delay);
	}

errorDeinit:

	ESP_LOGI(TAG, "Running Deinitialization");
	WS2812B.deInit(&ws2812);

	ESP_LOGI(TAG, "Deleting Task Handler");
	vTaskDelete(NULL);
}
```

目前为止我们实现了支持定时操作的LED灯。

#### 开机启动脚本与文件系统

完成上述的工程已经是一个较为完整的操作系统，可以在此框架下实现各种复杂的功能，然而，与Linux系统还有个明显的缺陷，就在于它没有“文件系统”。文件系统的好处在于它的灵活性，就比如开机启动脚本，我们不希望每一次改变开机启动脚本都需要重新烧录程序，而想要想Linux一样，通过vim修改文件就可以。为了实现这个功能，我们需要解决Flash本身存在性能缺陷的问题：写入速度远远慢于读出速度，而写入寿命只有短短的10万次。那么给予Flash的固态硬盘是如何实现的呢？它的实现比较复杂，会将文件尽可能写在那些比较新的块上，于是整个Flash每个块被写的次数几乎相同，这样就极大地增加了寿命，并且，不会出现少量几个不可用的块导致文件出现错误。我们使用了vfs（虚拟文件系统），并用了wear-leveling优化Flash的写入。

#### 实现LED灯的驱动

WS2812是一种全彩LED灯珠（256 * 256 * 256色），它的优势在于只需要一个GPIO就可以控制1000个LED灯珠，并且每个的颜色都不相同。它的实现原理如下：

![](p1.png)

![](p2.png)

![](p3.png)

引脚封装为：

![](p4.png)

数据传输通过：吃掉一份数据，并将剩下的转发的方式实现了高速方便的控制。然而观察到时间的控制非常严格，达到了百ns的级别，已经是二十分之一的系统周期，如果控制灯就要让CPU一直在工作而不能被打断，这样一来操作系统就不能适用（它的GPIO操作封装可能会导致无法忍受的延时），为了解决这个难题，我们尝试了两种方式：增加一片外置的MCU和使用RMT控制器。

1. 我们采用了不带操作系统的STM32，使用UART来控制，STM32通过c语言内嵌汇编`__nop()`操作来调节延时，通过示波器调节到了20ns偏差的量级，但最终会有一些问题：STM32的串口中断会将发送打断，导致频繁改变的颜色会出现闪烁。
2. 采用RMT+DMA的方式，用ESP32自带的外设来实现。DMA（直接内存获取）可以在CPU不参与的情况下直接读取内存，非常适合耗时硬件外设的控制。RMT是红外的收发模块，可以编解码，其特点是信号的形状可以自定义（不像UART、SPI等已经是严格的标准）。使用DMA的RMT可以以非常高的速度来改变GPIO，这样一来就可以控制WS2812了。

STM32的程序

```c
#define func(R) setWS(1); \
if(R & 0x80){__nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); \
	__nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); setWS(0); \
	__nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); \
	__nop(); __nop(); __nop(); __nop(); __nop(); __nop(); } \
else {setWS(0);       __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); \
	__nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); \
	__nop(); __nop(); __nop(); __nop(); __nop();} R <<= 1

void WS2812chars(char R, char G, char B) {
	func(G); func(G); func(G); func(G); func(G); func(G); func(G); func(G);
	func(R); func(R); func(R); func(R); func(R); func(R); func(R); func(R);
	func(B); func(B); func(B); func(B); func(B); func(B); func(B); func(B);
}
```

ESP32的程序

```c
void WS2812B_init(rmt_channel_t channel, gpio_num_t gpio, unsigned int size, rmt_item32_t** itemsp)	{
 	// ........
	rmt_config_t rmt_tx;
	memset(&rmt_tx, 0, sizeof(rmt_config_t));

	rmt_tx.channel = channel;
	rmt_tx.gpio_num = gpio;
	rmt_tx.mem_block_num = 1;
	rmt_tx.clk_div = 1;
	rmt_tx.tx_config.idle_output_en = 1;

	rmt_config(&rmt_tx);
	rmt_driver_install(rmt_tx.channel, 0, 0);
  	// ........
}
static void WS2812B_setLeds(wsRGB_t* data, unsigned int size, rmt_item32_t* items, rmt_channel_t channel) {
  	unsigned int itemCnt = 0;
	for(int i = 0; i < size; i++)
		for(int j = 0; j < 24; j++)
		{
			if(j < 8)
			{
				if(data[i].r & (1<<(7-j))) items[itemCnt++] = wsLogicOne;
				else items[itemCnt++] = wsLogicZero;
			}

			else if (j < 16)
			{
				if(data[i].g & (1<<(7 - (j%8) ))) items[itemCnt++] = wsLogicOne;
				else items[itemCnt++] = wsLogicZero;
			}
			else
			{
				if(data[i].b & (1<<( 7 - (j%8) ))) items[itemCnt++] = wsLogicOne;
				else items[itemCnt++] = wsLogicZero;
			}
		}
	rmt_write_items(channel, items, size * 24, false);
}
```

事实发现ESP32的程序工作得更稳定，其充分地利用了硬件外设。

### 硬件部分

设计一个外形独特的台灯，为了简化，它是没有底座的，贴在学习桌侧面的墙上，灯的角度可以通过步进电机改变，可以”摇头晃脑“地提醒人们。同时硬件上还留有LED显示屏，但本项目中没有遇到

#### 3D打印外壳

设计3D模型并用3D打印机打印出来

![](wx1.jpg)

![](wx3.jpg)

![](wx4.jpg)

![](wx5.jpg)

![](wx6.jpg)

中间调试RMT的输出波形

![](wx2.jpg)

