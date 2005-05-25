import re

bad_words = [re.compile(x, re.I) for x in [
    "texas.hold",
    "online.poker",
    "^<h1>",
    "highprofitclub",
#    "you are invited to visit (the sites about|some helpful info)",
#    "in your free time, check the sites dedicated",
    "3.card.poker",
    "phentermine",
    "hydrocone",
    "hydrocodone",
    "doobu.com",
    "nutzu.com",
    "construction-equipment-resources.com",
    "freemoney.com",
    " cialis ",
    "percocet",
    "pinpain.com",
    "shop263.com",
    "free.roulette",
    "online.casino",
    "highest.payout",
    "internet.casino",
    "online.wines",
    "casino.bonus",
    "kohavi",
    "penis.enlargement",
    ".yoll.net",
    "levitra",
    "vardenafil",
    "sildenafil",
    "ofloxacin",
    "oxybutynin",
    ".nicis-shop.de",
    "lawn-care-system",
    "hair-restoration",
    "excellent(meds|pills).com",
    "generalsteel",
    "general steel",
    "qualityrxpills.com",
    "discount-pills.biz",
    " vicodin ",
    "birthcpills.com",
    "dvd.netleih.de",
    "intimplace.com",
    "quality-generic.com",
    
    ]]

def is_spam(*words):
    for matcher in bad_words:
        for word in words:
            if matcher.search(word):
                return 1
    return 0
