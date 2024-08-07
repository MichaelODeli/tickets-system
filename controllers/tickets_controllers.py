from controllers import db_connection
import pandas as pd
from uuid import uuid4
from dash import no_update, html


def get_query_strings(
    mode, query_filter, limit=5, offset=0, ticket_uuid="", user_id=None
):
    limits = f"LIMIT {limit} OFFSET {offset}"
    orderby = "ORDER BY priority_id DESC, created_at DESC"
    where = ""

    orderby_without_priority = "ORDER BY created_at DESC"
    if mode == "multi":
        table_name = "tickets"
        if query_filter == "unanswered":
            where = "where step_id = 0"
        elif query_filter == "in_work":
            where = "where step_id = 1"
        elif query_filter == "ended":
            where = "where step_id = 2"
        elif query_filter in [
            "account_last5sended",
            "account_last5awaiting",
            "account_last5ended",
        ]:
            table_name = f"(select * from tickets where reporter_id = {user_id})"
            orderby = orderby_without_priority
            if query_filter == "account_last5sended":
                where = "where step_id = 0"
            if query_filter == "account_last5awaiting":
                where = "where step_id = 1"
            if query_filter == "account_last5ended":
                where = "where step_id = 2"
        else:
            table_name = "tickets"
    if mode == "single" and query_filter == "by_uuid":
        table_name = f"(select * from tickets where uuid = '{ticket_uuid}')"

    query_string = f"""SELECT * FROM {table_name} t 
    left join (select id as probl_id, problem_name from problems_list) p on t.problem_id = p.probl_id 
    left join (select id as prior_id, priority_name from priority_list) pi on pi.prior_id = t.priority_id 
    left join (select id as rep_id, username, first_name, middle_name, last_name, position_id, email from users) u on u.rep_id = t.reporter_id 
    left join (select id as pos_id, department_id, position_name from positions) po on u.position_id = po.pos_id
    left join (select id as dep_id, department_name from departments) d on d.dep_id = po.department_id
    left join (select id as stat_id, status_name, step_id from status_list) s on s.stat_id = t.status_id
    {where}
    {orderby} 
    {limits};""".replace(
        "\n", ""
    )
    len_query_string = f"SELECT count(*) FROM {table_name};"

    # print(query_string)

    return query_string, len_query_string


def filter_and_rename_df(
    df,
    mode="milti",
    multi_reports_columns=[
        "id",
        "Дата и время создания",
        "ФИО",
        "Название проблемы",
        "Приоритет",
        "Содержание отчета (сокр.)",
        "Текущий статус обращения",
    ],
    single_report_columns=[
        "id",
        "Дата и время создания",
        "ФИО (полное)",
        "Должность",
        "Отдел",
        "Приоритет",
        "Название проблемы",
        "Содержание отчета (полн.)",
        "Почта для связи",
        "Текущий статус обращения",
    ],
):
    if len(df) == 0:
        return df
    df["id"] = df["uuid"]
    df["created_at"] = df["created_at"].dt.strftime("%d.%m.%Y %H:%M:%S")

    # удаление ненужных колонок
    df.drop(
        columns=(
            [
                "prior_id",
                "priority_id",
                "probl_id",
                "problem_id",
                "rep_id",
                "reporter_id",
                "pos_id",
                "position_id",
                "dep_id",
                "department_id",
                "stat_id",
                "status_id",
                "username",
                "uuid",
            ]
        ),
        inplace=True,
    )
    # переименование
    df.rename(
        columns={
            "created_at": "Дата и время создания",
            "priority_name": "Приоритет",
            "problem_name": "Название проблемы",
            "text": "Содержание отчета (полн.)",
            "username": "Пользователь",
            "last_name": "Фамилия",
            "first_name": "Имя",
            "middle_name": "Отчество",
            "department_name": "Отдел",
            "position_name": "Должность",
            "email": "Почта для связи",
            "status_name": "Текущий статус обращения",
        },
        inplace=True,
    )
    df["Содержание отчета (сокр.)"] = df["Содержание отчета (полн.)"].apply(
        lambda x: x[:25] + "..." if len(x) > 25 else x
    )
    df["ФИО"] = (
        df["Фамилия"]
        + " "
        + df["Имя"].str.slice(0, 1)
        + ". "
        + df["Отчество"].str.slice(0, 1)
        + ". "
    )
    df["ФИО (полное)"] = df["Фамилия"] + " " + df["Имя"] + " " + df["Отчество"]
    df.drop(columns=["Фамилия", "Имя", "Отчество"], inplace=True)

    if mode == "single":
        return df[single_report_columns]
    if mode == "multi":
        return df[multi_reports_columns]


def get_tickets_info(
    return_df=True,
    mode="multi",
    query_filter="all",
    limit=5,
    offset=0,
    ticket_uuid=None,
    user_id=None,
):
    conn = db_connection.get_conn()
    query_string, len_query_string = get_query_strings(
        mode=mode,
        limit=limit,
        offset=offset,
        user_id=user_id,
        ticket_uuid=ticket_uuid,
        query_filter=query_filter,
    )

    records = pd.read_sql(len_query_string, conn)["count"].tolist()[0]

    # print(query_string)

    df = pd.read_sql_query(
        query_string,
        conn,
    )

    if len(df) == 0:
        df = pd.DataFrame(columns=["id", "По данному запросу нет данных"])

    # return only needed data
    if return_df:
        return filter_and_rename_df(df, mode="multi"), records
    else:
        return filter_and_rename_df(df, mode="single").to_dict("records")[0]


def get_ticket_history(ticket_uuid):
    conn = db_connection.get_conn()

    query_string = f"""select * from (select * from tickets_review where uuid = '{ticket_uuid}') tr
    left join (select id as rev_id, first_name, middle_name, last_name, position_id from users) u on u.rev_id = tr.reviewer_id
    left join (select id as pos_id, position_name from positions) po on u.position_id = po.pos_id
    left join (select id as stat_id, status_name, step_id from status_list) s on s.stat_id = tr.assigned_status
    order by updated_at asc;"""

    df = pd.read_sql_query(query_string, conn)
    df["created_at"] = df["created_at"].dt.strftime("%d.%m.%Y %H:%M:%S")
    df["updated_at"] = df["updated_at"].dt.strftime("%d.%m.%Y %H:%M:%S")
    df["FIO"] = (
        df["last_name"]
        + " "
        + df["first_name"].str.slice(0, 1)
        + ". "
        + df["middle_name"].str.slice(0, 1)
        + ". "
    )

    created = (
        df[df["step_id"] == 0].to_dict("records")[0]
        if len(df[df["step_id"] == 0]) > 0
        else pd.DataFrame()
    )
    in_work = (
        df[df["step_id"] == 1].to_dict("records")
        if len(df[df["step_id"] == 1]) > 0
        else pd.DataFrame()
    )
    ended = (
        df[df["step_id"] == 2].to_dict("records")[0]
        if len(df[df["step_id"] == 2]) > 0
        else pd.DataFrame()
    )

    return created, in_work, ended


def send_ticket(userdata, priority, problem, text, opened):
    try:
        ticket_uuid = str(uuid4())
        conn = db_connection.get_conn()
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO "tickets" '
                '("uuid", "reporter_id", "priority_id", "problem_id", "text") '
                "values (%(uuid)s, %(reporter_id)s, %(priority_id)s, %(problem_id)s, %(text)s);",
                {
                    "uuid": ticket_uuid,
                    "reporter_id": userdata["user_id"],
                    "priority_id": int(priority),
                    "problem_id": int(problem),
                    "text": text,
                },
            )
        conn.commit()
        conn.close()
        return "", ticket_uuid, not opened
    except Exception:
        return (
            "Ошибка отправки. Повторите позднее.",
            no_update,
            no_update,
        )


def send_ticket_answer(ans_text, status, report_link, t_uuid, userdata):
    try:
        conn = db_connection.get_conn()
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO "tickets_review" '
                '("uuid", "reviewer_id", "assigned_status", "text") '
                "values (%(uuid)s, %(reviewer_id)s, %(assigned_status)s, %(text)s);",
                {
                    "uuid": t_uuid,
                    "reviewer_id": userdata["user_id"],
                    "assigned_status": int(status),
                    "text": ans_text,
                },
            )
        conn.commit()
        conn.close()
        return (
            [
                "Ответ успешно отправлен. ",
                html.A(
                    "Откройте данный тикет в новой вкладке для продолжения работы.",
                    href=report_link,
                    target="_blank",
                ),
            ],
            "green",
            0,
        )
    except Exception:
        return (
            [
                "Ошибка отправки попробуйте позднее."
            ],
            "red",
            0,
        )
