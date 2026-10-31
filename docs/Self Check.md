Week 7

https://chat.deepseek.com/share/hfottssl5nyu47609o


১. কেন Service Layer-এ HTTPException থ্রো করলাম না?
২. DELETE রিকোয়েস্টে 204 স্ট্যাটাস কোড কেন ব্যবহার করা হয়?
৩. get_contract_by_id-এ আমরা কেন শুধু id দিয়ে খুঁজছি না, user_id == user_id চেক করছি কেন? (Security)

<details> <summary>উত্তর</summary>
১. কারণ Service Layer হলো পিওর বিজনেস লজিক। HTTPException হলো FastAPI-এর একটি ক্লাস। সার্ভিস লেয়ার যদি HTTPException জানে, তবে ভবিষ্যতে এই সার্ভিস যদি কোনো CLI বা gRPC-তে ব্যবহার করতে চাই, তবে সেখানে FastAPI-এর ইম্পোর্ট এরর দেবে (Coupling)। তাই সার্ভিস শুধু None রিটার্ন করে, আর রাউটার সেটাকে HTTP 404-এ কনভার্ট করে।
২. কারণ ডিলিট করার পর ক্লায়েন্টকে আর কোনো ডেটা বা বডি ফেরত দেওয়ার দরকার নেই। ২০৪ মানে "সফল, কিন্তু কোনো কন্টেন্ট নেই।"
৩. এটি অত্যন্ত জরুরি সিকিউরিটি চেক (IDOR - Insecure Direct Object Reference)। যদি শুধু id দিয়ে খুঁজি, তবে ইউজার A, ইউজার B-এর কন্ট্র্যাক্ট আইডি অনুমান করে (যেমন 1, 2, 3) সরাসরি তার ডেটা দেখে ফেলতে পারে। তাই WHERE id=X AND user_id=Y চেক করা হয় যাতে ইউজার শুধু নিজের ডেটাই অ্যাক্সেস করে।