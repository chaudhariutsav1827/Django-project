from django.shortcuts import render,redirect
import random
from .models import User,Product,Wishlist,Cart,Transaction
from django.conf import settings
from django.core.mail import send_mail
from .paytm import generate_checksum, verify_checksum
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
# Create your views here.

def initiate_payment(request):
    try:
        user=User.objects.get(email=request.session['email'])
        amount = int(request.POST['amount'])
        
    except:
        return render(request, 'payments/pay.html', context={'error': 'Wrong Accound Details or amount'})

    transaction = Transaction.objects.create(made_by=user,amount=amount)
    transaction.save()
    merchant_key = settings.PAYTM_SECRET_KEY

    params = (
        ('MID', settings.PAYTM_MERCHANT_ID),
        ('ORDER_ID', str(transaction.order_id)),
        ('CUST_ID', str('chaudhariutsav1827@gmail.com')),
        ('TXN_AMOUNT', str(transaction.amount)),
        ('CHANNEL_ID', settings.PAYTM_CHANNEL_ID),
        ('WEBSITE', settings.PAYTM_WEBSITE),
        # ('EMAIL', request.user.email),
        # ('MOBILE_N0', '9911223388'),
        ('INDUSTRY_TYPE_ID', settings.PAYTM_INDUSTRY_TYPE_ID),
        ('CALLBACK_URL', 'http://127.0.0.1:8000/callback/'),
        # ('PAYMENT_MODE_ONLY', 'NO'),
    )

    paytm_params = dict(params)
    checksum = generate_checksum(paytm_params, merchant_key)

    transaction.checksum = checksum
    transaction.save()
    carts=Cart.objects.filter(user=user,payment_status=False)
    for i in carts:
    	i.payment_status=True
    	i.save()
    carts=Cart.objects.filter(user=user,payment_status=False)
    request.session['cart_count']=len(carts)
    paytm_params['CHECKSUMHASH'] = checksum
    print('SENT: ', checksum)
    return render(request, 'redirect.html', context=paytm_params)

@csrf_exempt
def callback(request):
    if request.method == 'POST':
        received_data = dict(request.POST)
        paytm_params = {}
        paytm_checksum = received_data['CHECKSUMHASH'][0]
        for key, value in received_data.items():
            if key == 'CHECKSUMHASH':
                paytm_checksum = value[0]
            else:
                paytm_params[key] = str(value[0])
        # Verify checksum
        is_valid_checksum = verify_checksum(paytm_params, settings.PAYTM_SECRET_KEY, str(paytm_checksum))
        if is_valid_checksum:
            received_data['message'] = "Checksum Matched"
        else:
            received_data['message'] = "Checksum Mismatched"
            return render(request, 'callback.html', context=received_data)
        return render(request, 'callback.html', context=received_data)

def index(request):
	try:
		user=User.objects.get(email=request.session['email'])
		if user.usertype == 'seller':
			return render(request,'seller_index.html')
		else:
			return render(request,'index.html')
	except:
		return render(request,'index.html')
def about(request):
	return render(request,'about.html')

def computer(request):
	return render(request,'computer.html')

def laptop(request):
	return render(request,'laptop.html')

def product(request):
	return render(request,'product.html')

def contact(request):
	if request.method=='POST':
		subject = 'Welcome'
		message = 'Hi ,'+request.POST['name']+', Welcome To Cla. Your Request Has Been Recieved Successfully.'
		email_from = settings.EMAIL_HOST_USER
		recipient_list = [request.POST['email'], ]
		send_mail( subject, message, email_from, recipient_list )
		return render(request,'contact.html',{'msg':'Contecected successfully'})
	else:
		return render(request,'contact.html')

def login(request):
	if request.method=="POST":
		try:
			user=User.objects.get(email=request.POST['email'],
								  password=request.POST['password']
								  )
			wishlists=Wishlist.objects.filter(user=user)
			carts=Cart.objects.filter(user=user,payment_status=False)
			if user.usertype=="user":
				request.session['email']=user.email
				request.session['fname']=user.fname
				request.session['profile_pic']=user.profile_pic.url
				request.session['wishlist_count']=len(wishlists)
				request.session['cart_count']=len(carts)
				return render(request,'index.html')
			else:
				request.session['email']=user.email
				request.session['fname']=user.fname
				request.session['profile_pic']=user.profile_pic.url
				return render(request,'seller_index.html')				
		except Exception as e:
			print(e)
			msg="Email or Password is incorrect"
			return render(request,'login.html',{'msg':msg})
	else:
		return render(request,'login.html')

def signup(request):
	if request.method=='POST':			
		try:
			User.objects.get(email=request.POST['email'])
			msg='Email is already registered'
			return render(request,'signup.html',{'msg':msg})
		except:	
			if request.POST['password']==request.POST['cpassword']:	
				User.objects.create(
				usertype=request.POST['usertype'],
				fname=request.POST['fname'],
				lname=request.POST['lname'],  
				email=request.POST['email'],
				mobile=request.POST['mobile'],
				address=request.POST['address'],
				password=request.POST['password'],
				profile_pic=request.FILES['profile_pic']
				)
				msg='Signed up successfully'
				return render(request,'login.html',{'msg':msg})	
			else:
				msg='Password & Confirm Password does not match'	
				return render(request,'signup.html',{'msg':msg})
	else:
		return render(request,'signup.html')

def change_password(request):
	if request.method=='POST':
		user=User.objects.get(email=request.session['email'])
		if request.POST['old_password']==user.password:
			if request.POST['new_password']==request.POST['cnew_password']:
				user.password=request.POST['new_password']
				user.save()
				return redirect('logout')
			else:
				msg="New password & Confirm New password does not match"
				return render(request,'change_password.html',{'msg':msg})
		else:
			msg="Old password does not match"
			return render(request,'change_password.html',{'msg':msg})
	else:
		return render(request,'change_password.html')

def seller_change_password(request):
	if request.method=='POST':
		user=User.objects.get(email=request.session['email'])
		if request.POST['old_password']==user.password:
			if request.POST['new_password']==request.POST['cnew_password']:
				user.password=request.POST['new_password']
				user.save()
				return redirect('logout')
			else:
				msg="New password & Confirm New password does not match"
				return render(request,'seller_change_password.html',{'msg':msg})
		else:
			msg="Old password does not match"
			return render(request,'seller_change_password.html',{'msg':msg})
	else:
		return render(request,'seller_change_password.html')

def seller_index(request):
	return render(request,'seller_index.html')

def logout(request):
	try:
		del request.session['email']
		del request.session['fname']
		del request.session['profile_pic']
		del request.session['wishlist_count']
		del request.session['cart_count']
		return render(request,'login.html')
	except:	
		return render(request,'login.html')

def forgot_password(request):
	if request.method=="POST":
		try:
			user=User.objects.get(email=request.POST['email'])
			otp=random.randint(1000,9999)
			subject = 'OTP For Forgot Password'
			message = 'Hi ,'+user.fname+', Here is your OTP for forgot password is  '+ str(otp)
			email_from = settings.EMAIL_HOST_USER
			recipient_list = [user.email, ]
			msg='OTP sent successfully'
			send_mail( subject, message, email_from, recipient_list )
			return render(request,'otp.html',{'email':user.email,'otp':otp})
		except:
			msg="Email does not registered"
			return render(request,'forgot_password.html',{'msg':msg})
	else:
		return render(request,'forgot_password.html')

def otp(request):
	uotp=request.POST['uotp']
	otp=request.POST['otp']
	email=request.POST['email']
	if otp==uotp:
		return render(request,'new_password.html',{'email':email})
	else:
		msg="OTP Is Incorrect"
		return render(request,'otp.html',{'msg':msg,'otp':otp,'email':email})

def new_password(request):
	if request.POST['new_password']==request.POST['cnew_password']:
		user=User.objects.get(email=request.POST['email'])
		user.password=request.POST['new_password']
		user.save()
		msg='Password updated successfully'
		return render(request,'login.html',{'msg':msg})
	else:
		msg='New Password & Confirm new password does not match'
		return render(request,'new_password.html',{'msg':msg,'email':request.POST['email']})

def profile_pic(request):
	user=User.objects.get(email=request.session['email'])
	if request.method=="POST":
		user.fname=request.POST['fname']
		user.lname=request.POST['lname']
		user.mobile=request.POST['mobile']
		user.address=request.POST['address']
		user.profile_pic=request.FILES['profile_pic']
		user.save()
		del request.session['profile_pic']
		request.session['profile_pic']=user.profile_pic.url
		msg="Profile Updated Successfully"
		return render(request,'profile_pic.html',{'msg':msg,'user':user})
	else:
		return render(request,'profile_pic.html',{'user':user})

def seller_add_product(request):
	seller=User.objects.get(email=request.session['email'])
	if request.method=="POST":
		discounted_price=(int(request.POST['product_price']))*(int(request.POST['product_discount']))/100
		discounted_price=(int(request.POST['product_price']))-discounted_price
		Product.objects.create(
			seller=seller,
			product_category=request.POST['product_category'],
			product_name=request.POST['product_name'],
			product_price=request.POST['product_price'],
			product_discount=request.POST['product_discount'],
			product_discount_price=discounted_price,
			product_desc=request.POST['product_desc'],
			product_image=request.FILES['product_image']
			)
		msg="Product Added Successfully"
		return render(request,'seller_add_product.html',{'msg':msg})
	else:
		return render(request,'seller_add_product.html')

def product_by_category(request,pc):
	products=Product.objects.filter(product_category=pc)
	return render(request,'view_product.html',{'products': products,'pc':pc})

def seller_view_product(request):
	seller=User.objects.get(email=request.session['email'])
	products=Product.objects.filter(seller=seller)
	return render(request,'seller_view_product.html',{'products':products})

def seller_product_details(request,pk):
	product=Product.objects.get(pk=pk)
	return render(request,'seller_product_details.html',{'product':product})

def product_details(request,pk):
	wishlist_flag=False
	cart_flag=False
	product=Product.objects.get(pk=pk)
	try:
		user=User.objects.get(email=request.session['email'])
		Wishlist.objects.get(user=user,product=product)
		wishlist_flag=True
	except:
		pass
	try:
		user=User.objects.get(email=request.session['email'])
		Cart.objects.get(user=user,product=product,payment_status=False)
		cart_flag=True
	except:
		pass
	return render(request,'product_details.html',{'product':product,'wishlist_flag':wishlist_flag,'cart_flag':cart_flag})

def seller_edit_product(request,pk):
	product=Product.objects.get(pk=pk)
	if request.method=="POST":
		product.product_category=request.POST['product_category']
		product.product_name=request.POST['product_name']
		product.product_price=request.POST['product_price']
		product.product_discount=request.POST['product_discount']
		product.product_desc=request.POST['product_desc']
		try:
			product.product_image=request.FILES['product_image']
		except:
			pass
		product.save()
		msg="Product Edited Successfully"
		return render(request,'seller_edit_product.html',{'product': product,'msg':msg})
	else:
		return render(request,'seller_edit_product.html',{'product': product})

def seller_delet_product(request,pk):
	product=Product.objects.get(pk=pk)
	product.delete()
	return redirect('seller_view_product')

def add_to_wishlist(request,pk):
	user=User.objects.get(email=request.session['email'])
	product=Product.objects.get(pk=pk)
	Wishlist.objects.create(user=user,product=product)
	request.session['wishlist_count']+=1
	return redirect('wishlist')

def wishlist(request):
	user=User.objects.get(email=request.session['email'])
	wishlists=Wishlist.objects.filter(user=user)
	request.session['wishlist_count']=len(wishlists)
	return render(request,'wishlist.html',{'wishlists':wishlists})

def remove_from_wishlist(request,pk):
	user=User.objects.get(email=request.session['email'])
	product=Product.objects.get(pk=pk)
	wishlist=Wishlist.objects.get(user=user,product=product)
	wishlist.delete()
	request.session['wishlist_count']-=1
	return redirect('wishlist')

def cart(request):
	net_price=0
	user=User.objects.get(email=request.session['email'])
	carts=Cart.objects.filter(user=user,payment_status=False)
	for i in carts:
		net_price=net_price+i.total_price
	return render(request,'cart.html',{'carts':carts,'net_price':net_price})

def add_to_cart(request,pk):
	user=User.objects.get(email=request.session['email'])
	product=Product.objects.get(pk=pk)
	Cart.objects.create(
		user=user,
		product=product,
		product_price=product.product_price,
		total_price=product.product_price,
		payment_status=False
		)
	request.session['cart_count']+=1
	return redirect('cart')

def remove_from_cart(request,pk):
	user=User.objects.get(email=request.session['email'])
	product=Product.objects.get(pk=pk)
	cart=Cart.objects.get(user=user,product=product)
	cart.delete()
	request.session['cart_count']-=1
	return redirect('cart')

def change_qty(request,pk):
	cart=Cart.objects.get(pk=pk)
	cart.product_qty=int(request.POST['product_qty'])
	cart.total_price=int(request.POST['product_qty'])*cart.product_price
	cart.save()
	return redirect('cart')

def my_order(request):
	user=User.objects.get(email=request.session['email'])
	carts=Cart.objects.filter(user=user,payment_status=True)
	return render(request,'my_order.html',{'carts':carts})

def validate_email(request):
	email=request.GET.get('email')
	data={
		'is_taken':User.objects.filter(email__iexact=email).exists()
	}
	return JsonResponse(data)

def subscribe(request):
	subject = 'Welcome'
	message = 'Hello User ,'', You Have Successfully Subscribed To Our Services.'
	email_from = settings.EMAIL_HOST_USER
	recipient_list = [request.POST['email'], ]
	send_mail( subject, message, email_from, recipient_list )
	return render(request,'index.html')