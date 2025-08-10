#hello do i get the change

class checktheday:
    def __init__(self):
        pass
    def date(self):
        date = int(input("enter the date"))
        if 0 > date or date > 31:
            print("enter a valid date")
        return date%7

    def checkleap(self,k):
        return (k % 4 == 0 and (k % 100 != 0 or k % 400 == 0))

    def month(self):
        mont = int(input("enter month number"))
        if mont < 0 or 12 < mont:
            return "enter a valid month"
        
        l = str(mont)
        nonleap = {
            "1": 1,
            "2":4,
            "3":4,
            "4":0,
            "5":2,
            "6": 5,
            "7":0,
            "8":3,
            "9":6,
            "10":1,
            "11": 4,
            "12":6,
        }
        leap = {
            "1": 0,
            "2":3,
            "3":4,
            "4":0,
            "5":2,
            "6": 5,
            "7":0,
            "8":3,
            "9":6,
            "10":1,
            "11": 4,
            "12":6,

        }
        if self.checkleap(self.y) == True:
            return leap[l]
        return leap[l]



    def year(self):
        self.y = int(input("enter the year"))
        if  self.y <= 1200 or self.y >= 2800:
            return("enter a valid year in between 18s to 20s")
        k = str(self.y)
        j = (k[:2])
        (last) = k[2:]
        (last_digit) = int(last)
        rem = (last_digit%7)
        qutiont = (last_digit//4)
        d = {
            "12" :-1,
            "13" : 4,
            "14" : +2,
            "15" :0,
            "16":-1,
            "17": 4,
            "18" : +2,
            "19" : 0,
            "20" : -1,
            "21" : +4,
            "22" : +2,
            "23" : 0,
            "24" :-1,
            "25" : +4,
            "26" : +2,
            "27" : 0,
            "28" :1,
        }
        
        final = ((d[j]+rem+qutiont) + self.month() +self.date())%7
        try :

            if final == 1:
                return "sunday"
            elif final == 2:
                return "monday"
            elif final == 3:
                return "tuesday"
            elif final == 4:
                return "wednesday"
            elif final == 5:
                return "Thrusday"
            elif final == 6:
                return "friday"
            elif final == 7:
                return "saturday"
            else:
                return "you have entered someting wrong"
        except :
            print("you enterd soemthing wrong")
       


    
s = checktheday()
print(s.year())
    


    
    

