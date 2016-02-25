DBHOST = '127.0.0.1'
DBUSER = 'root'
DBPW = 'root'
DBNAME = 'xojdb'
DBPORT = 3306
PROBLEMS_PER_PAGE = 20
CONTESTS_PER_PAGE = 10
USERS_PER_PAGE = 20
STATUS_PER_PAGE = 10
JUDGER = ['http://localhost:8088/judger']
COOKIESECRET = 'top-secret'
JUDGER_KEY = 'top-secret'
MYURL = 'http://localhost:5000/'
DEFAULT_CONTENT = r'''###**题目描述**

给你两个整数A和B，求A+B的值。

###**输入格式**

一行，空格隔开的两个整数A和B。

###**输出格式**

一行一个整数，表示答案。

###**样例输入**

```
233 233
```

###**样例输出**

```
466
```

###**数据范围与约定**

对于100%的数据，$0 \le A,B \le 10^9$

###**提示**

你可以提交下面的代码通过本题。

```c++
#include<cstdio>
int main(){  // ← 注意不要换行
    int a,b;
    scanf("%d%d",&a,&b);
    printf("%d\n",a+b);
    return 0;
}
```'''

