def generate_final_feedback(total_score):

    if total_score >= 90:
        return "Outstanding performance! You are interview ready 🚀"

    elif total_score >= 70:
        return "Good performance! Improve explanation depth."

    elif total_score >= 50:
        return "Average performance. Focus on fundamentals."

    else:
        return "Needs improvement. Revise core concepts."

# def generate_final_feedback(total_score):
#     if total_score > 80:
#         return "Excellent performance! You are industry ready 🚀"
#     elif total_score > 60:
#         return "Good work! Improve communication & depth."
#     else:
#         return "Focus on fundamentals and project explanation."