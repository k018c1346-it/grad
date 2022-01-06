from datetime import datetime, timedelta
import os
from re import template
from uuid import uuid4
from flask import (
    Blueprint, abort, request, render_template,
    redirect, url_for, flash
)
from flask.globals import session
from flask_login import (
    login_user, login_required, logout_user, current_user
)
from flaskr.models import (
    User, PasswordResetToken,Planning_data,Comment_data,Message_data,Planning_menber,
    Planning_chat,Plan_evaluation,User_evaluation,End_plan_data,Sharing_initiatives
)
from flaskr import db

from flaskr.forms import (
    LoginForm, RegisterForm, ResetPasswordForm,
    ForgotPasswordForm, UserForm, ChangePasswordForm
)

bp = Blueprint('app', __name__, url_prefix='')


dict ={'放送芸術科':'カメラマン 放送制作 映像編集 放送音声','声優・演劇科':'声優 俳優・タレント',
'演劇スタッフ科':'演劇','マンガ・アニメーション科':'キャラクターデザイン マンガ アニメーション','ゲームクリエイター科':'ゲームプログラマー ゲームプランナー ゲームCGデザイナー ゲームビジネス',
'CG映像科':'CG映像','デザイン科':'グラフィックデザイン イラストレーション インテリアデザイン プロダクトデザイン','ミュージックアーティスト科':'ギター ベース ドラム キーボード ヴォーカル 作詞・作曲',
'音響芸術科':'TV映像音楽クリエイター ゲーム音楽クリエイター','コンサート・イベント科':'コンサート制作 コンサートPA コンサート照明 コンサート舞台 イベント企画 音響芸術','ダンスパフォーマンス科':'ダンスパフォーマンス',
'ITスペシャリスト科(4年制)':'システム モバイルアプリ ネットワークセキュリティー webデザイン','情報処理科':'システム モバイルアプリ webデザイン','情報ビジネス科':'システム モバイルアプリ webデザイン','AIシステム科':'システム モバイルアプリ','ネットワークセキュリティ科':'ネットワークセキュリティー',
'建築学科(4年制)':'建築設計 機械設計','建築設計科':'機械設計','機械設計科':'建築設計','電子・電気科':'電子・電気科'}
course_cr = ['放送芸術科','声優・演劇科','演劇スタッフ科','マンガ・アニメーション科']
course_ds = ['ゲームクリエイター科','CG映像科','デザイン科']
course_mu = ['ミュージックアーティスト科','音響芸術科','コンサート・イベント科','ダンスパフォーマンス科']
course_it = ['ITスペシャリスト科(4年制)','情報処理科','情報ビジネス科','AIシステム科','ネットワークセキュリティ科']
course_tc = ['建築学科(4年制)','建築設計科','機械設計科','電子・電気科']
tagu = ['カメラマン','放送制作','映像編集','放送音声','放送照明','映像美術','声優','俳優・タレント'
    ,'演劇','キャラクターデザイン','マンガ','アニメーション','ゲームプログラマー','ゲームプランナー','ゲームCGデザイナー','ゲームビジネス','CG映像'
,'グラフィックデザイン','イラストレーション','インテリアデザイン','プロダクトデザイン','ギター','ベース','ドラム','キーボード','ヴォーカル','作詞・作曲','TV映像音楽クリエイター',
'ゲーム音楽クリエイター','コンサート制作','コンサートPA','コンサート照明','コンサート舞台','イベント企画','音響芸術','ダンスパフォーマンス','システム','モバイルアプリ','ネットワークセキュリティー','webデザイン','建築設計','機械設計','電子・電気科']
@bp.route('/')
def home():
    #
    plan = Planning_data.select_home()
    end_lists = Planning_data.end_select_home()
    recommended_projects = ""
    if current_user.is_authenticated:
        my_tags = User.select_profile(current_user.id)
        for i in my_tags:
            tags = i.taglist.split(',')
            recommended_projects = Planning_data.recommended_plan(tags)
    html = 'home.html'
    return render_template(html,tag=tagu,course_cr=course_cr,course_ds=course_ds,
    course_mu=course_mu,course_it=course_it,course_tc=course_tc,lists=plan,end_lists=end_lists,
    recommended_projects=recommended_projects)
    #
#プロフィールページ遷移
@bp.route('/mypage')
def mypage():
    profile = User.select_profile(current_user.id)
    for file in profile:
        comment = file.comment
        if file.taglist != 'null':
            current_tag = file.taglist.split(',')
    print(current_tag)
    plan = Planning_data.profail_plan(current_user.id)
    participation_plan = Planning_data.select_participation_plan(current_user.id)
    print(participation_plan)
    html = "mypage.html"
    return render_template(html,profile=profile,current_tag=current_tag,plan=plan,participation_plan=participation_plan,comment=comment)

#共有ページ
@bp.route('/sharing')
def sharing():
    plan_lists = Planning_data.my_end_plan_list(current_user.id)
    participation_lists = Planning_data.my_end_plan_participation_list(current_user.id)
    html = 'sharing.html'
    print(participation_lists)
    return render_template(html,plan_lists=plan_lists,participation_lists=participation_lists)

#URL発行
@bp.route('/shar',methods=["POST"])
def shar():
    plan_list = ""
    if request.form.getlist("plan_id"):
        plan_list = request.form.getlist("plan_id")
    plan_list = ",".join(plan_list)
    print(plan_list)
    token = ""
    token = str(uuid4())
    print(token)
    new_token = Sharing_initiatives(
        token= token,
        user_id=current_user.id,
        plan_list=plan_list,
        expire_at=datetime.now() + timedelta(days=14)
    )
    new_token.publish_token()
    db.session.commit()
    print(
            f'パスワード設定用URL: http://127.0.0.1:5000/sharing/{token}'
        )
    return redirect(url_for('app.home'))

@bp.route('/sharing/<uuid:token>')
def sharing_uuid(token):
    sharing_plan_lists = Sharing_initiatives.get_plan_lists(token)
    for plan in sharing_plan_lists:
        user_id = plan.user_id
        files = Planning_data.id_serect_multiple(plan.plan_list)
    user = User.select_profile(user_id)
    html = 'sharing_profile.html'
    return render_template(html,user=user,user_id=user_id,files=files,token=token)

@bp.route('/end_details/<uuid:token>')
def end_details_uuid(token):
    id = request.args.get('ID')
    sharing_plan_lists = Sharing_initiatives.get_plan_lists(token)
    for plan in sharing_plan_lists:
        plan_list = plan.plan_list.split(',')
    for i in plan_list:
        if i == id:
            #企画内容
            html = 'sharing_end_details.html'
            lists = Planning_data.id_serect(id)
            comment = Comment_data.select_comment_date(id)
            menber = Planning_menber.plan_member(id)
            end_plan_image = End_plan_data.images_list(id)
            evaluation = Plan_evaluation.evaluation_search(id)
            #チャット内容
            chat_list = Planning_chat.select_plan_chat(id)
            planner_list = Planning_data.select_planner(id)
            plan_member = Planning_menber.plan_member(id)
            for i in planner_list:
                planner = int(i.planner)
            #評価点数の平均
            eva = 0
            for i in evaluation:
                eva += int(i.evaluation)
            eva = eva / len(evaluation)
            if current_user.is_authenticated:
                flag_1 = Message_data.application_confirmation(id,current_user.id)
                # 企画タグを,ごとに区切りリストに登録
            for i in lists:
                planning_tag = i.taglist.split(',')
                planner_id = int(i.planner)
                flag = i.flag
            for i in end_plan_image:
                if i.image:
                    image_lists = i.image.split(',')
                    video = i.video
            return render_template(html,tag=tagu,lists=lists,planning_tag=planning_tag,id=id,comment=comment,planner_id=planner_id,
            menber_list=menber,flag=flag,flag_1=flag_1,image_lists=image_lists,video=video,eva=eva,chat_list=chat_list,plan_member=plan_member,planner=planner,planner_list=planner_list)
    return redirect(url_for('app.home'))

@bp.route('/練習')
def 練習():
    plan = User.select_all()
    a = Planning_data.select_all()
    create_plan = Planning_menber.select_id_by_title("送信練習")
    print(create_plan)
    html = '練習.html'
    picture_path = User.select_picture_path(current_user.id)
    for i in picture_path:
        picture_path = i.picture_path
    return render_template(html, user=plan, a=a, picture_path=picture_path)

@bp.route('/練習_s', methods=["POST"])
def 練習1():
    for i in range(5):
        f = request.form.get(str(i))
        print(f)
    plan = User.select_all()
    a = Planning_data.select_all()
    html = '練習.html'
    picture_path = User.select_picture_path(current_user.id)
    for i in picture_path:
        picture_path = i.picture_path
    return render_template(html, user=plan, a=a, picture_path=picture_path)

@bp.route('/練習_f', methods=["POST"])
def 練習_f():
    if request.method == 'POST':
        files = request.files.getlist('file')
        for file in files:
            imagename = file.filename
            print(imagename)
            new_dir_path = "flaskr/static/練習/"
            os.makedirs(new_dir_path, exist_ok=True)
            if imagename:
                file.save(new_dir_path +'/'+ imagename)
    return redirect(url_for('app.練習'))

@bp.route('/logout')
def logout():
    logout_user() # ログアウト
    return redirect(url_for('app.home'))

@bp.route('/search')
def search():
    html = 'search.html'
    tag =''
    cla =''
    if request.args.get('class'):
        cl = request.args.get('class')
        cla = cl
        cl = dict[cl].split(' ') 
        lists = Planning_data.class_search(cl)
    else:
        tag = request.args.get('tags')
        lists = Planning_data.select_search(tag)
    return render_template(html, tag=tag, taglist=tagu, lists=lists,cla =cla)

@bp.route('/planning_list')
@login_required
def planning_list():
    html = 'planning_list.html'
    lists = Planning_data.my_planning_list(current_user.id)
    return render_template(html, lists=lists)

@bp.route('/participation_list')
@login_required
def participation_list():
    html = 'participation_list.html'
    lists = Planning_data.participation_list(current_user.id)
    return render_template(html, lists=lists)

@bp.route('/plan_chat')
@login_required
def plan_chat():
    id = request.args.get('ID')
    check = Planning_menber.check_menber(id,current_user.id)
    lists = Planning_chat.select_plan_chat(id)
    planner = Planning_data.select_planner(id)
    member_status = Planning_menber.menber_status(id,current_user.id)
    planning_status = Planning_data.plan_status(id)
    plan_data = Planning_data.id_serect(id)
    plan_member = Planning_menber.plan_member(id)
    member_flag = Plan_evaluation.member_flag(id)
    for i in planner:
        plan = int(i.planner)
        flag = i.flag

    for i in member_flag:
        if i.user_id == str(current_user.id):
            return redirect(url_for('app.end_details')+'?ID='+id)
    
    print(member_status,planning_status)
    print(member_flag)
    #プロジェクトフラグが「3」の時、評価画面に遷移
    if flag == '3' or flag == '4':
        #プロジェクトフラグ「3」で企画者であれば提出フォームに進む
        if flag == '3' and plan == current_user.id:
            html = 'propose.html'
        else:
            html = 'evaluation.html'
        member = Planning_menber.plan_member(id)
        member_len = len(member)
        current = str(current_user.id)
        return render_template(html,lists=lists,id=id,plan=plan,plan_data=plan_data,planner=planner,member=member,member_len=member_len,current=current,plan_member=plan_member)
    #プロジェクトメンバーか企画者ならば、プランチャットに遷移
    if check > 0 or plan == current_user.id:
        html = 'plan_chat.html'
        return render_template(html,lists=lists,id=id,plan=plan,plan_data=plan_data,planner=planner,plan_member=plan_member)
    return redirect(url_for('app.home'))

#企画のフラグを終了にする。（3）
@bp.route('/end_plan', methods=["POST"])
@login_required
def end_plan():
    id = request.form.get('id')
    #フラグを[3]にする。終了状態。
    Planning_data.change_flag(id,'3')
    db.session.commit()
    #ソースコードの登録画面。

    return redirect(url_for('app.plan_chat')+'?ID='+id)

#成果物の画像と動画を保存する。
@bp.route('end_plan_upload', methods=["POST"])
@login_required
def end_plan_upload():
    l = []
    v = []
    lists = 'null'
    videos = 'null'
    id = request.form.get('id')
    files = request.files.getlist('file')
    s_files = request.files.getlist('s_file')

    if not len(files[0].filename) == 0:
        for file in files:
            imagename = file.filename
            l.append(imagename)
            print(l) 
            new_dir_path = "flaskr/static/end_plan/" + id + "/image/"
            os.makedirs(new_dir_path, exist_ok=True)
            if imagename:
                file.save(new_dir_path +'/'+ imagename)
            lists = ','.join(l)
            print(lists)
    if not len(s_files[0].filename) == 0:
        for file in s_files:
            videoname = file.filename
            v.append(videoname)
            print(v) 
            new_dir_path = "flaskr/static/end_plan/" + id + "/video/"
            os.makedirs(new_dir_path, exist_ok=True)
            if videoname:
                file.save(new_dir_path +'/'+ videoname)
            videos = ','.join(v)

    end_plan = End_plan_data(
        plan_id=id,
        image=lists,
        video=videos
    )
    end_plan.add_end_plan()
    db.session.commit()

    #flagを変更
    Planning_data.change_flag(id,'4')
    db.session.commit()
    return redirect(url_for('app.plan_chat')+'?ID='+id)
#チャット書き込み処理
@bp.route('/plan_chat_up', methods=["POST"])
@login_required
def plan_chat_up():
    if request.method == "POST":
        id = request.form.get('ID')
        Name_id = request.form.get('Name_id')
        comment = request.form.get('comment')
        files = request.files.getlist('file')
        print()
        l = []
        if comment:
            chat = Planning_chat(
                plan_id=id,
                member_id = Name_id,
                comment = comment,
                flag = "0"
            )
            chat.add_plan_chat()
            db.session.commit()
        if not len(files[0].filename) == 0:
            for file in files:
                imagename = file.filename
                l.append(imagename)
                print(l) 

                new_dir_path = "flaskr/static/plan_chat/" + id + "/"
                os.makedirs(new_dir_path, exist_ok=True)
                if imagename:
                    file.save(new_dir_path +'/'+ imagename)
            lists = ','.join(l)
            print(lists)
            chat = Planning_chat(
                plan_id=id,
                member_id = Name_id,
                comment = lists,
                flag = "1"
            )
            chat.add_plan_chat()
            db.session.commit()
            
        
    return redirect(url_for('app.plan_chat')+'?ID='+id)

#評価ページ処理
@bp.route('/planning_evaluation', methods=["POST"])
@login_required
def planning_evaluation():
    planning_evaluation = request.form.get("planning_number")
    id = request.form.get("id")
    planning_comment = request.form.get("planning_comment")
    #企画への評価
    add_plan_evaluation = Plan_evaluation(
        plan_id = id,
        user_id = current_user.id,
        evaluation = planning_evaluation,
        comment = planning_comment
    )
    add_plan_evaluation.evaluation_add()
    db.session.commit()
    #企画者への評価
    planner = Planning_data.select_planner(id)
    for i in planner:
        plan = i.planner
    if current_user.id != plan:
        print(plan)
        user_add = User_evaluation(
            plan_id = id,
            receiver = plan,
            sender = current_user.id,
            evaluation = request.form.get("planner_number"),
            comment = request.form.get("planner_comment")
        )
        user_add.user_evaluation_add()
        db.session.commit()
    member = Planning_menber.plan_member(id)
    print(planning_evaluation,planning_comment)
    print(len(member))
    #メンバーの評価
    if len(member) > 0:
        for i in member:
            m = request.form.get(i.member_id + "_number")
            comment = request.form.get(i.member_id + "_comment")
            user_add = User_evaluation(
            plan_id = id,
            receiver = request.form.get(i.member_id),
            sender = current_user.id,
            evaluation = request.form.get(i.member_id + "_number"),
            comment = request.form.get(i.member_id + "_comment")
        )
            print(m)
            print(comment)
    if str(current_user.id) != plan:
        Planning_menber.menber_flags(id,current_user.id,"3")
        db.session.commit()
    else:
        Planning_data.change_flag(id,"4")
        db.session.commit()
    return redirect(url_for('app.plan_chat')+'?ID='+id)
    

#企画詳細ページの処理
@bp.route('/details')
def details():
    if request.method == 'GET':
        id = request.args.get('ID')
    lists = Planning_data.id_serect(id)
    comment = Comment_data.select_comment_date(id)
    menber = Planning_menber.plan_member(id)
    flag_1 = ""
    planning_tag = ''
    if current_user:
        if current_user.is_authenticated:
            flag_1 = Message_data.application_confirmation(id,current_user.id)
        # 企画タグを,ごとに区切りリストに登録
    for i in lists:
        if i.taglist != 'null' and i.taglist:
            planning_tag = i.taglist.split(',')
        planner_id = int(i.planner)
        flag = i.flag
    html = 'details.html'
    return render_template(html,tag=tagu,course_cr=course_cr,course_ds=course_ds,
    course_mu=course_mu,course_it=course_it,course_tc=course_tc,lists=lists,planning_tag=planning_tag,id=id,comment=comment,planner_id=planner_id,
    menber_list=menber,flag=flag,flag_1=flag_1)

    #企画詳細ページの処理
@bp.route('/end_details')
def end_details():
    if request.method == 'GET':
        id = request.args.get('ID')
    lists = Planning_data.id_serect(id)
    comment = Comment_data.select_comment_date(id)
    menber = Planning_menber.plan_member(id)
    end_plan_image = End_plan_data.images_list(id)
    evaluation = Plan_evaluation.evaluation_search(id)
    planning_tag = 'null'
    #評価点数の平均
    eva = 0
    for i in evaluation:
        eva += int(i.evaluation)
    eva = eva / len(evaluation)
        # 企画タグを,ごとに区切りリストに登録
    for i in lists:
        if i.taglist != 'null' and i.taglist:
            planning_tag = i.taglist.split(',')
        planner_id = int(i.planner)
        flag = i.flag
    for i in end_plan_image:
        if i.image:
            image_lists = i.image.split(',')
            video = i.video
    print(image_lists)
    html = 'end_details.html'
    return render_template(html,tag=tagu,course_cr=course_cr,course_ds=course_ds,
    course_mu=course_mu,course_it=course_it,course_tc=course_tc,lists=lists,planning_tag=planning_tag,id=id,comment=comment,planner_id=planner_id,
    menber_list=menber,flag=flag,image_lists=image_lists,video=video,eva=eva)

#動作確認
@bp.route('/practic')
def practic():
    if request.method == 'GET':
        id = request.args.get('ID')
    lists = Planning_data.id_serect(id)
    menber = Planning_menber.plan_menber(id)
    print(menber)
        # 企画タグを,ごとに区切りリストに登録
    for i in lists:
        planner_id = int(i.planner)
    html = '練習.html'
    return render_template(html,tag=tagu,lists=lists,menber=menber,id=id,planner_id=planner_id)

@bp.route('/practic_end', methods=["POST"])
def practic_end():
    id = request.args.get('ID')
    menber = Planning_menber.plan_menber(id)
    for i in menber:
        print(i.member_id)
        recipient_name_id = request.form.get(2)
        print(recipient_name_id)
    return redirect(url_for('app.practic')+'?ID='+id)


@bp.route('/deadline')
@login_required
def deadline():
    id = request.args.get('ID')
    Planning_data.change_flag(id,"1")
    db.session.commit()
    return redirect(url_for('app.details')+'?ID='+id)

#申請メッセージの送信
@bp.route('/send_message', methods=["POST"])
@login_required
def send_message():
    id = request.form.get('ID')
    recipient_name_id = request.form.get('recipient_name_id')
    message = request.form.get('message-text')
    sender_name_id = request.form.get('sender_name_id')
    message_add = Message_data(
        plan_id=id,
        recipient_name_id = recipient_name_id,
        sender_name_id = sender_name_id,
        message = message
    )
    menber = Planning_menber(
        plan_id = id,
        member_id = current_user.id,
        flag = '0'
    )
    menber.menber_add()
    db.session.commit()
    message_add.create_new_message()
    db.session.commit()
    return redirect(url_for('app.details')+'?ID='+id)

@bp.route('/message_details')
@login_required
def message_details():
    id = request.args.get('ID')
    message = Message_data.details_message(id)
    print(message)
    return render_template('message_details.html',message=message)

@bp.route('/plan_request_ok')
@login_required
def plan_request_ok():
    flag = '1'
    id = request.args.get('ID')
    Planning_menber.menber_flag(id,flag)
    db.session.commit()
    return redirect(url_for('app.message_details')+'?ID='+id)

@bp.route('/plan_request_ng')
@login_required
def plan_request_ng():
    flag = '2'
    id = request.args.get('ID')
    Planning_menber.menber_flag(id,flag)
    db.session.commit()
    return redirect(url_for('app.message_details')+'?ID='+id)

@bp.route('/plan_request')
@login_required
def plan_request():
    flag = '0'
    id = request.args.get('ID')
    Planning_menber.menber_flag(id,flag)
    db.session.commit()
    return redirect(url_for('app.message_details')+'?ID='+id)

@bp.route('/message_list')
@login_required
def message_list():
    userid = current_user.id
    message_list = Message_data.select_recipient_message(userid)
    html = 'message_list.html'
    print(userid)
    print(message_list)
    return render_template(html,message_list=message_list)


@bp.route('/comment', methods=["POST"])
@login_required
def comment():
    id = request.form.get('ID')
    Name_id = request.form.get('Name_id')
    comment = request.form.get('comment')
    plan = Comment_data(
        plan_id=id,
        user_id = Name_id,
        comment = comment
    )
    plan.create_new_comment()
    db.session.commit()
    return redirect(url_for('app.details')+'?ID='+id)

@bp.route('/delete')
def delete():
    id = request.args.get('ID')
    Planning_data.delete_plan(id)
    return redirect(url_for('app.home'))

@bp.route('/update')
def update():
    id = request.args.get('ID')
    plan = Planning_data.id_serect(id)
    html = 'update.html'
    return render_template(html,plan=plan)

@bp.route('/updated',methods=["POST"])
def updated():
    id = request.args.get('ID')
    title = str(request.form.get('title'))
    contents = request.form.get('contents')
    application = request.form.get('application')
    taglist = request.form.get('taglist')
    print(title)
    Planning_data.update_plan(id,title,contents,application,taglist)
    db.session.commit()
    return redirect(url_for('app.home'))

#投稿ホーム
@bp.route('/forms')
@login_required
def forms():
    html = 'forms.html'
    return render_template(html, tag=tagu)
    

#データーベースに登録
@bp.route('/decision',methods=["POST"])
def decision():
    image = request.files['image']
    imagename = image.filename
    title = request.form.get('title')
    taglist = "null"
    if request.form.getlist("fav"):
        taglist = request.form.getlist("fav")
        print("favs:", taglist)
        if request.form.get('taglist'):
            l = request.form.get('taglist').split(',')
            print(l)
            taglist = taglist + l
            print(taglist)
            taglist = ",".join(taglist)
            #taglist = taglist.append(request.form.get('taglist').split(','))
    elif request.form.get('taglist'):
        taglist = request.form.get('taglist').split(',')
        taglist = ",".join(taglist)
    #test1テーブルにインサート
    plan = Planning_data(
        title,
        contents = request.form.get('contents'),
        application = request.form.get('application'),
        planner = current_user.id,
        image = imagename,
        taglist = taglist,
        flag = '1'
        
    )
    plan.create_new_plan()
    db.session.commit()
    create_plan = Planning_data.select_create_at(title)
    #IDを表示
    print(create_plan)
    ID = str(create_plan.id)
    new_dir_path = "flaskr/static/planning_image/" + ID
    os.makedirs(new_dir_path, exist_ok=True)
    if imagename:
        image.save(new_dir_path +'/'+ imagename)
    return redirect(url_for('app.home'))

@bp.route('/confirm',methods=["POST"])
def confirm():
    taglist = "null"
    image = request.files['image']
    imagename = image.filename
    user_id = request.form.get('user_id')
    user_name = request.form.get('user_name')
    password = request.form.get('password')
    comment = request.form.get('comment')

    if request.form.getlist("fav"):
        taglist = request.form.getlist("fav")
        print("favs:", taglist)
        if request.form.get('taglist'):
            l = request.form.get('taglist').split(',')
            print(l)
            taglist = taglist + l
            print(taglist)
            #taglist = taglist.append(request.form.get('taglist').split(','))
    elif request.form.get('taglist'):
        taglist = request.form.get('taglist').split(',')
    taglist = ",".join(taglist)

    User.save_profile(user_id,user_name,imagename,taglist,password,comment)
    db.session.commit()
    new_dir_path = "flaskr/static/user_image/" + user_id
    os.makedirs(new_dir_path, exist_ok=True)
    if imagename:
        image.save(new_dir_path +'/'+ imagename)
    return redirect(url_for('app.home'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    #form = LoginForm(request.form)
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.select_user_by_email(email)
        password = request.form.get('password')
        if user and user.is_active and user.validate_password(password):
            login_user(user, remember=True)
            next = request.args.get('next')
            if not next:
                next = url_for('app.home')
            return redirect(next)
        elif not user:
            flash('存在しないユーザです')
        elif not user.is_active:
            flash('無効なユーザです。パスワードを再設定してください')
        elif not user.validate_password(password):
            flash('メールアドレスとパスワードの組み合わせが誤っています')
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    #form = RegisterForm(request.form)
    if request.method == 'POST':
        user = User(
            username = request.form.get('username'),
            email = request.form.get('email')
        )
        with db.session.begin(subtransactions=True):
            user.create_new_user()
        db.session.commit()
        token = ''
        with db.session.begin(subtransactions=True):
            token = PasswordResetToken.publish_token(user)
        db.session.commit()
        # メールに飛ばすほうがいい
        print(
            f'パスワード設定用URL: http://127.0.0.1:5000/reset_password/{token}'
        )
        return redirect(url_for('app.login'))
    return render_template('register.html')

@bp.route('/reset_password/<uuid:token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_user_id = PasswordResetToken.get_user_id_by_token(token)
    if not reset_user_id:
        abort(500)
    print(reset_user_id)
    return render_template('reset_password.html', tag=tagu,reset_user_id=reset_user_id)

@bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm(request.form)
    if request.method == 'POST' and form.validate():
        email = form.email.data
        user = User.select_user_by_email(email)
        if user:
            with db.session.begin(subtransactions=True):
                token = PasswordResetToken.publish_token(user)
            db.session.commit()
            reset_url = f'http://127.0.0.1:5000/reset_password/{token}'
            print(reset_url)
            flash('パスワード再登録用のURLを発行しました。')
        else:
            flash('存在しないユーザです')
    return render_template('forgot_password.html', form=form)

@bp.route('/user', methods=['GET', 'POST'])
@login_required
def user():
    form = UserForm(request.form)
    if request.method == 'POST' and form.validate():
        user_id = current_user.get_id()
        user = User.select_user_by_id(user_id)
        with db.session.begin(subtransactions=True):
            user.username = form.username.data
            user.email = form.email.data
            file = request.files[form.picture_path.name].read()
            if file:
                file_name = user_id + '_' + \
                    str(int(datetime.now().timestamp())) + '.jpg'
                picture_path = 'flaskr/static/user_image/' + file_name
                open(picture_path, 'wb').write(file)
                user.picture_path = 'user_image/' + file_name
        db.session.commit()
        flash('ユーザ情報の更新に成功しました')
    return render_template('user.html', form=form)

@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User.select_user_by_id(current_user.get_id())
        password = form.password.data
        with db.session.begin(subtransactions=True):
            user.save_new_password(password)
        db.session.commit()
        flash('パスワードの更新に成功しました')
        return redirect(url_for('app.user'))
    return render_template('change_password.html', form=form)