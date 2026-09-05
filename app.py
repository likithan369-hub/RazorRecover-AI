import streamlit as st
import pandas as pd
import os
import sys

# --------------------------------------------------
# ADD BACKEND FOLDER TO PYTHON PATH
# --------------------------------------------------

sys.path.append(
    os.path.join(os.path.dirname(__file__), "backend")
)

from agent import predict_recovery, choose_intervention
from policies import check_policy
from recovery_executor import (
    execute_recovery,
    check_payment_status
)


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="RazorRecover AI",
    page_icon="💰",
    layout="wide"
)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

DATA_PATH = "data/transactions.csv"
AUDIT_PATH = "data/audit_trail.csv"

df = pd.read_csv(DATA_PATH)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("💰 RazorRecover AI")

st.subheader(
    "AI-Powered Revenue Recovery Agent"
)

st.write(
    "Detect revenue at risk, determine the safest recovery "
    "intervention, and execute bounded recovery workflows."
)


# --------------------------------------------------
# METRICS
# --------------------------------------------------

at_risk = df[
    df["transaction_status"] != "Success"
]

revenue_at_risk = at_risk["amount"].sum()


# Load latest audit trail
if os.path.exists(AUDIT_PATH):

    audit_df = pd.read_csv(
        AUDIT_PATH
    )

else:

    audit_df = pd.DataFrame()


# Revenue recovered
if (
    not audit_df.empty
    and "recovered_amount" in audit_df.columns
):

    revenue_recovered = pd.to_numeric(
        audit_df["recovered_amount"],
        errors="coerce"
    ).fillna(0).sum()

else:

    revenue_recovered = 0


recovery_rate = (
    revenue_recovered / revenue_at_risk * 100
    if revenue_at_risk > 0
    else 0
)


col1, col2, col3, col4 = st.columns(4)


col1.metric(
    "Revenue at Risk",
    f"₹{revenue_at_risk:,.0f}"
)


col2.metric(
    "Revenue Recovered",
    f"₹{revenue_recovered:,.0f}"
)


col3.metric(
    "Recovery Rate",
    f"{recovery_rate:.2f}%"
)


col4.metric(
    "At-Risk Transactions",
    f"{len(at_risk):,}"
)


st.divider()


# --------------------------------------------------
# AI RECOVERY ANALYZER
# --------------------------------------------------

st.header(
    "🤖 AI Recovery Analyzer"
)


transaction_id = st.selectbox(
    "Select a transaction",
    at_risk["transaction_id"].tolist()
)


selected_transaction = at_risk[
    at_risk["transaction_id"] == transaction_id
].iloc[0].to_dict()


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "analysis_result" not in st.session_state:

    st.session_state.analysis_result = None


if "execution_result" not in st.session_state:

    st.session_state.execution_result = None


if "payment_result" not in st.session_state:

    st.session_state.payment_result = None


# --------------------------------------------------
# ANALYZE TRANSACTION
# --------------------------------------------------

if st.button(
    "Analyze Transaction",
    type="primary"
):

    probability = predict_recovery(
        selected_transaction
    )


    action = choose_intervention(
        selected_transaction,
        probability
    )


    allowed, reason = check_policy(
        selected_transaction,
        action
    )


    st.session_state.analysis_result = {

        "transaction": selected_transaction,

        "probability": probability,

        "action": action,

        "allowed": allowed,

        "reason": reason
    }


    # Clear old execution/payment results
    st.session_state.execution_result = None

    st.session_state.payment_result = None


# --------------------------------------------------
# SHOW ANALYSIS
# --------------------------------------------------

if st.session_state.analysis_result is not None:

    result = st.session_state.analysis_result


    transaction = result["transaction"]

    probability = result["probability"]

    action = result["action"]

    allowed = result["allowed"]

    reason = result["reason"]


    # --------------------------------------------------
    # TRANSACTION DETAILS
    # --------------------------------------------------

    st.subheader(
        "Transaction Details"
    )


    col1, col2, col3 = st.columns(3)


    col1.metric(
        "Amount",
        f"₹{transaction['amount']:,.2f}"
    )


    col2.metric(
        "Status",
        transaction["transaction_status"]
    )


    col3.metric(
        "Retry Count",
        transaction["retry_count"]
    )


    st.divider()


    # --------------------------------------------------
    # AI DECISION
    # --------------------------------------------------

    st.subheader(
        "AI Decision"
    )


    col1, col2 = st.columns(2)


    with col1:

        st.metric(
            "Recovery Probability",
            f"{probability * 100:.2f}%"
        )


    with col2:

        st.metric(
            "Recommended Action",
            action
        )


    # --------------------------------------------------
    # GUARDRAIL
    # --------------------------------------------------

    st.subheader(
        "🛡️ Guardrail"
    )


    if not allowed:

        st.error(
            f"🚫 BLOCKED — {reason}"
        )

        st.warning(
            "No payment action was executed because "
            "the guardrail blocked the request."
        )


    else:

        st.success(
            f"✅ ALLOWED — {reason}"
        )


        # ==================================================
        # RECOVERY EXECUTION
        # ==================================================

        st.divider()

        st.subheader(
            "⚡ Recovery Execution"
        )


        # --------------------------------------------------
        # ACTION-SPECIFIC INFORMATION
        # --------------------------------------------------

        if action == "ESCALATE":

            st.warning(
                "⚠️ AI recommends escalation. "
                "No automatic payment action will be executed."
            )


        elif action == "SEND_REMINDER":

            st.info(
                "📩 AI recommends sending a payment reminder."
            )


        elif action == "RETRY_PAYMENT":

            st.info(
                "🔄 AI recommends a bounded payment retry."
            )


        elif action == "SEND_PAYMENT_LINK":

            st.info(
                "💳 AI recommends creating a Razorpay "
                "Test Mode payment link."
            )


        # --------------------------------------------------
        # EXECUTE BUTTON
        # --------------------------------------------------

        if st.session_state.execution_result is None:

            if st.button(
                "🚀 Execute Recovery",
                type="primary",
                key="execute_recovery_button"
            ):

                with st.spinner(
                    "Executing recovery action..."
                ):

                    execution_result = execute_recovery(
                        transaction,
                        action
                    )


                st.session_state.execution_result = (
                    execution_result
                )

                st.rerun()


        # --------------------------------------------------
        # SHOW EXECUTION RESULT
        # --------------------------------------------------

        execution_result = (
            st.session_state.execution_result
        )


        if execution_result is not None:


            # ==============================================
            # ALREADY RECOVERED
            # ==============================================

            if execution_result["status"] == "ALREADY_RECOVERED":

                st.warning(
                    "🛡️ Already Recovered"
                )

                st.info(
                    execution_result["message"]
                )


            # ==============================================
            # PAYMENT LINK CREATED
            # ==============================================

            elif (
                execution_result["status"]
                == "PAYMENT_LINK_CREATED"
            ):

                st.success(
                    "✅ Recovery payment link "
                    "created successfully!"
                )


                st.subheader(
                    "💳 Payment Link"
                )


                col1, col2, col3 = st.columns(3)


                with col1:

                    st.metric(
                        "Payment Link ID",
                        execution_result[
                            "payment_link_id"
                        ]
                    )


                with col2:

                    st.metric(
                        "Amount",
                        f"₹{transaction['amount']:,.2f}"
                    )


                with col3:

                    st.metric(
                        "Status",
                        execution_result["status"]
                    )


                st.write("")


                # ------------------------------------------
                # OPEN PAYMENT LINK
                # ------------------------------------------

                st.link_button(
                    "🔗 Open Razorpay Payment Link",
                    execution_result[
                        "payment_link"
                    ],
                    type="primary"
                )


                st.caption(
                    "This is a Razorpay Test Mode "
                    "payment link. No real money will "
                    "be charged."
                )


                st.info(
                    "💡 Creating the payment link does "
                    "not mean revenue has been recovered. "
                    "Revenue is counted only after a "
                    "successful payment."
                )


                # ------------------------------------------
                # PAYMENT VERIFICATION
                # ------------------------------------------

                st.divider()

                st.subheader(
                    "🔍 Payment Verification"
                )


                if st.button(
                    "🔍 Check Payment Status",
                    key="check_payment_status_button"
                ):

                    with st.spinner(
                        "Checking payment status with Razorpay..."
                    ):

                        payment_result = (
                            check_payment_status(
                                execution_result[
                                    "payment_link_id"
                                ]
                            )
                        )


                    st.session_state.payment_result = (
                        payment_result
                    )


                    st.rerun()


                # ------------------------------------------
                # SHOW PAYMENT RESULT
                # ------------------------------------------

                payment_result = (
                    st.session_state.payment_result
                )


                if payment_result is not None:


                    # --------------------------------------
                    # PAYMENT SUCCESS
                    # --------------------------------------

                    if (
                        payment_result["status"]
                        == "SUCCESS"
                    ):

                        st.success(
                            "✅ Payment successfully received!"
                        )


                        st.metric(
                            "Revenue Recovered",
                            f"₹{payment_result['paid_amount']:,.2f}"
                        )


                        st.write(
                            "Payment Status: "
                            f"**{payment_result['payment_status']}**"
                        )


                    # --------------------------------------
                    # PAYMENT PENDING
                    # --------------------------------------

                    elif (
                        payment_result["status"]
                        == "PENDING"
                    ):

                        st.warning(
                            "⏳ Payment has not been "
                            "completed yet."
                        )


                        st.write(
                            "Payment Status: "
                            f"**{payment_result['payment_status']}**"
                        )


                        st.metric(
                            "Revenue Recovered",
                            f"₹{payment_result['paid_amount']:,.2f}"
                        )


                    # --------------------------------------
                    # PAYMENT CHECK FAILED
                    # --------------------------------------

                    else:

                        st.error(
                            "❌ Could not verify payment: "
                            f"{payment_result['message']}"
                        )


            # ==============================================
            # RETRY SUCCESS
            # ==============================================

            elif execution_result["status"] == "SUCCESS":

                st.success(
                    "✅ Payment retry succeeded!"
                )


                st.metric(
                    "Revenue Recovered",
                    f"₹{execution_result['recovered_amount']:,.2f}"
                )


                st.info(
                    execution_result["message"]
                )


            # ==============================================
            # RETRY FAILED
            # ==============================================

            elif (
                execution_result["status"] == "FAILED"
                and action == "RETRY_PAYMENT"
            ):

                st.error(
                    "❌ Payment retry failed"
                )


                st.write(
                    execution_result["message"]
                )


            # ==============================================
            # ESCALATION
            # ==============================================

            elif action == "ESCALATE":

                st.warning(
                    "🚨 Case Escalated"
                )


                st.info(
                    "This transaction has been escalated "
                    "to the merchant for manual review. "
                    "No automatic payment action was executed."
                )


            # ==============================================
            # OTHER FAILED EXECUTION
            # ==============================================

            elif execution_result["status"] == "FAILED":

                st.error(
                    "❌ Recovery execution failed: "
                    f"{execution_result['message']}"
                )


            # ==============================================
            # OTHER / SKIPPED
            # ==============================================

            else:

                st.info(
                    f"ℹ️ {execution_result['message']}"
                )


# --------------------------------------------------
# TRANSACTION OVERVIEW
# --------------------------------------------------

st.divider()

st.header(
    "📊 Transaction Overview"
)


status_counts = df[
    "transaction_status"
].value_counts()


st.bar_chart(
    status_counts
)


# --------------------------------------------------
# AI INTERVENTION STRATEGY
# --------------------------------------------------

st.divider()

st.header(
    "🤖 AI Intervention Strategy"
)


st.write(
    "Recovery actions selected by RazorRecover AI "
    "during the batch recovery process."
)


if (
    not audit_df.empty
    and "recommended_action" in audit_df.columns
):

    action_counts = (

        audit_df[
            "recommended_action"
        ]

        .value_counts()

        .rename_axis(
            "Recovery Action"
        )

        .reset_index(
            name="Transaction Count"
        )
    )


    if len(action_counts) > 0:

        cols = st.columns(
            len(action_counts)
        )


        for col, row in zip(
            cols,
            action_counts.itertuples(
                index=False
            )
        ):

            col.metric(
                row[0],
                f"{row[1]:,}"
            )


        st.write("")


        chart_data = action_counts.set_index(
            "Recovery Action"
        )


        st.bar_chart(
            chart_data,
            y="Transaction Count",
            width="stretch"
        )


    else:

        st.info(
            "No intervention strategy data available yet."
        )


else:

    st.info(
        "No intervention strategy data available yet."
    )


# --------------------------------------------------
# AUDIT TRAIL
# --------------------------------------------------

st.divider()

st.header(
    "📋 Audit Trail"
)


if os.path.exists(AUDIT_PATH):

    # Always load latest data
    audit_df = pd.read_csv(
        AUDIT_PATH
    )


    if not audit_df.empty:

        st.dataframe(
            audit_df.tail(100),
            width="stretch"
        )

    else:

        st.info(
            "No audit records available yet."
        )

else:

    st.info(
        "No audit records available yet."
    )


# --------------------------------------------------
# FAILURE HANDLING
# --------------------------------------------------

st.divider()

st.header(
    "🛡️ Failure Handling"
)


st.write(
    "RazorRecover AI follows a safe-stop policy "
    "when a payment API failure or uncertain "
    "payment state occurs."
)


st.code(
    """
AI Decision
     ↓
Payment Action
     ↓
API Failure / Timeout
     ↓
SAFE STOP
     ↓
Further retries blocked
     ↓
ESCALATE TO MERCHANT
     ↓
AUDIT TRAIL
""",
    language="text"
)


st.success(
    "Failure handling: SAFE STOP → ESCALATE → AUDIT"
)