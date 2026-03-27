import os
import logging
from telegram import Update, InputSticker
from telegram.ext import ContextTypes
from config.settings import ADMIN_IDS, STORAGE_DIR, STICKER_PACK_NAME
from .queue_manager import QueueManager

logger = logging.getLogger(__name__)

# Singletons (to be initialized by main)
queue_manager = QueueManager()

def admin_only(func):
    """Decorator to restrict commands to admins."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or update.effective_user.id not in ADMIN_IDS:
            logger.warning(f"Unauthorized access attempt by {update.effective_user.id if update.effective_user else 'Unknown'}")
            return
        return await func(update, context)
    return wrapper

@admin_only
async def pending_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all pending submissions."""
    pending = queue_manager.get_pending()
    if not pending:
        await update.message.reply_text("✅ No pending submissions.")
        return
    
    text = f"📋 **Pending Submissions ({len(pending)}):**\n\n"
    for sub in pending:
        text += f"ID: `{sub['id']}` - Emoji: {sub['emoji']}\nFrom: {sub['from_user_name']} (`{sub['from_user_id']}`)\n\n"
        # Prevent message from getting too long
        if len(text) > 3800:
            text += "... (and more)"
            break
            
    await update.message.reply_text(text, parse_mode="Markdown")

@admin_only
async def approve_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approves a single submission: /approve <id>"""
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /approve <id>")
        return
        
    sub_id = context.args[0]
    sub = queue_manager.get_submission(sub_id)
    
    if not sub:
        await update.message.reply_text("❌ Submssion not found.")
        return
        
    if sub["status"] != "pending":
        await update.message.reply_text(f"⚠️ Submission is already {sub['status']}.")
        return

    msg = await update.message.reply_text(f"⏳ Adding sticker `{sub_id}` to pack...", parse_mode="Markdown")

    try:
        # Add to pack via Bot API using file_id directly
        sticker = InputSticker(
            sticker=sub["file_id"],
            emoji_list=[sub["emoji"]],
            format="static"
        )
        await context.bot.add_sticker_to_set(
            user_id=sub["from_user_id"],
            name=STICKER_PACK_NAME,
            sticker=sticker
        )

        # Update queue
        queue_manager.update_status(sub_id, "approved")
        await msg.edit_text(f"✅ Submission `{sub_id}` approved and added to pack!", parse_mode="Markdown")

        # Notify user
        try:
            await context.bot.send_message(
                chat_id=sub["from_user_id"],
                text=f"🎉 *Good news!* Your sticker submission (`{sub_id}`) has been approved and added to the pack!",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify user {sub['from_user_id']}: {e}")

    except Exception as e:
        logger.error(f"Error approving {sub_id}: {e}")
        await msg.edit_text(f"❌ Error during approval: {e}")

@admin_only
async def reject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rejects a single submission: /reject <id> [reason]"""
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /reject <id> [reason]")
        return
        
    sub_id = context.args[0]
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided."
    
    sub = queue_manager.get_submission(sub_id)
    if not sub:
        await update.message.reply_text("❌ Submssion not found.")
        return
        
    if sub["status"] != "pending":
        await update.message.reply_text(f"⚠️ Submission is already {sub['status']}.")
        return

    # Update queue
    queue_manager.update_status(sub_id, "rejected", reason=reason)
    await update.message.reply_text(f"⛔️ Submission `{sub_id}` rejected.", parse_mode="Markdown")
    
    # Notify user (Phase 6)
    try:
        await context.bot.send_message(
            chat_id=sub["from_user_id"],
            text=f"⚠️ **Update on your submission:** Your sticker submission (`{sub_id}`) has been rejected.\n\n**Reason:** {reason}"
        )
    except Exception as e:
        logger.error(f"Failed to notify user {sub['from_user_id']}: {e}")

@admin_only
async def approveall_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bulk approve all pending."""
    pending = queue_manager.get_pending()
    if not pending:
        await update.message.reply_text("✅ No pending submissions.")
        return
        
    msg = await update.message.reply_text(f"⏳ Starting bulk approval of {len(pending)} submissions...")
    
    success_count = 0
    fail_count = 0
    
    for sub in pending:
        try:
            sticker = InputSticker(
                sticker=sub["file_id"],
                emoji_list=[sub["emoji"]],
                format="static"
            )
            await context.bot.add_sticker_to_set(
                user_id=sub["from_user_id"],
                name=STICKER_PACK_NAME,
                sticker=sticker
            )

            success_count += 1
            queue_manager.update_status(sub["id"], "approved")
            try:
                await context.bot.send_message(
                    chat_id=sub["from_user_id"],
                    text=f"🎉 **Good news!** Your sticker submission (`{sub['id']}`) has been approved and added to the pack!"
                )
            except:
                pass

        except Exception as e:
            logger.error(f"Bulk approve error on {sub['id']}: {e}")
            fail_count += 1
            
    await msg.edit_text(f"✅ Bulk approval finished!\n- Success: {success_count}\n- Failed: {fail_count}")

@admin_only
async def block_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Blocks a user from submitting: /block <user_id>"""
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /block <user_id>")
        return
        
    try:
        target_user = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ User ID must be a number.")
        return
        
    queue_manager.block_user(target_user)
    await update.message.reply_text(f"🛑 User `{target_user}` has been blocked from submitting.", parse_mode="Markdown")

@admin_only
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows bot usage statistics."""
    stats = queue_manager.get_stats()
    text = (
        "📊 **Bot Statistics**\n\n"
        f"Total Submissions: {stats['total']}\n"
        f"Pending: {stats['pending']}\n"
        f"Approved: {stats.get('approved', 0)}\n"
        f"Rejected: {stats.get('rejected', 0)}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

@admin_only
async def createpack_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Creates the sticker pack: /createpack. Requires you to send a sticker or image first as a reply."""
    user = update.effective_user

    # Need a first sticker to create a pack — use a simple 512x512 placeholder
    # The user must reply to a sticker/image with /createpack
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "⚠️ Reply to a sticker or image with /createpack to use it as the first sticker in the pack."
        )
        return

    reply = update.message.reply_to_message
    file_id = None
    if reply.sticker:
        file_id = reply.sticker.file_id
    elif reply.photo:
        file_id = reply.photo[-1].file_id
    elif reply.document:
        file_id = reply.document.file_id

    if not file_id:
        await update.message.reply_text("❌ The replied message doesn't contain a sticker or image.")
        return

    try:
        sticker = InputSticker(
            sticker=file_id,
            emoji_list=["😊"],
            format="static"
        )
        await context.bot.create_new_sticker_set(
            user_id=user.id,
            name=STICKER_PACK_NAME,
            title="HYC Sticker Pack",
            stickers=[sticker],
        )
        link = f"https://t.me/addstickers/{STICKER_PACK_NAME}"
        await update.message.reply_text(f"✅ Sticker pack created!\n\n{link}")
    except Exception as e:
        logger.error(f"Error creating sticker pack: {e}")
        await update.message.reply_text(f"❌ Failed to create pack: {e}")

@admin_only
async def packlink_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the sticker pack link."""
    from config.settings import STICKER_PACK_NAME
    link = f"https://t.me/addstickers/{STICKER_PACK_NAME}"
    await update.message.reply_text(f"📦 **Sticker Pack Link:**\n\n{link}", parse_mode="Markdown")
