#include "AshWellIntroHUD.h"
#include "AshWellChapterDirector.h"
#include "AshWellCombatCharacter.h"
#include "AshWellWarden.h"
#include "AshWellSession.h"
#include "AshWellIntroGameMode.h"
#include "GameFramework/PlayerController.h"

#include "CanvasItem.h"
#include "Dom/JsonObject.h"
#include "Engine/Canvas.h"
#include "Engine/Font.h"
#include "Engine/World.h"
#include "Fonts/CompositeFont.h"
#include "Fonts/SlateFontInfo.h"
#include "HAL/FileManager.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

namespace
{
    float CaptionEnvelope(float Elapsed, float Duration, float FadeIn, float FadeOut)
    {
        if (Elapsed < 0.0f || Elapsed >= Duration)
        {
            return 0.0f;
        }

        const float InAlpha = FMath::Clamp(Elapsed / FMath::Max(FadeIn, 0.001f), 0.0f, 1.0f);
        const float OutAlpha = FMath::Clamp((Duration - Elapsed) / FMath::Max(FadeOut, 0.001f), 0.0f, 1.0f);
        const float Alpha = FMath::Min(InAlpha, OutAlpha);
        return Alpha * Alpha * (3.0f - 2.0f * Alpha);
    }
}

AAshWellIntroHUD::AAshWellIntroHUD()
{
    bShowHUD = true;
}

void AAshWellIntroHUD::BeginPlay()
{
    Super::BeginPlay();
    bBeginPlayCalled = true;
    IntroStartTime = WorldTime();
    InitializeFont();
    WriteRuntimeSnapshot();
}

double AAshWellIntroHUD::WorldTime() const
{
    return GetWorld() ? static_cast<double>(GetWorld()->GetTimeSeconds()) : 0.0;
}

void AAshWellIntroHUD::InitializeFont()
{
    if (RuntimeCaptionFont)
    {
        return;
    }

    // A redistributable project font takes priority. The system path is only a
    // local editor fallback; packaged builds should include the project font.
    FontPath = FPaths::Combine(FPaths::ProjectContentDir(),
        TEXT("AshWell/Intro/Fonts/NotoSansSC-Regular.otf"));

#if PLATFORM_MAC
    if (!FPaths::FileExists(FontPath))
    {
        FontPath = TEXT("/System/Library/Fonts/Hiragino Sans GB.ttc");
    }
#endif

    if (!FPaths::FileExists(FontPath))
    {
        FontPath = FPaths::Combine(FPaths::EngineContentDir(),
            TEXT("Slate/Fonts/DroidSansFallback.ttf"));
    }

    FontPath = FPaths::ConvertRelativePathToFull(FontPath);
    // Canvas rejects an FSlateFontInfo whose FontObject is null, even when its
    // CompositeFont is valid. A runtime UFont supplies both the Canvas cache
    // type and the Chinese typeface used by Slate's glyph atlas.
    RuntimeCaptionFont = NewObject<UFont>(this, TEXT("IntroCaptionFont"));
    RuntimeCaptionFont->FontCacheType = EFontCacheType::Runtime;
    RuntimeCaptionFont->LegacyFontSize = 17;
    RuntimeCaptionFont->GetMutableInternalCompositeFont() = FCompositeFont(
        FName(TEXT("Regular")), FontPath, EFontHinting::Default, EFontLoadingPolicy::LazyLoad);
}

void AAshWellIntroHUD::SetSubtitle(const FString& Text, float DurationSeconds)
{
    Subtitle = Text;
    SubtitleDuration = FMath::Max(0.0f, DurationSeconds);
    SubtitleStartTime = WorldTime();
}

void AAshWellIntroHUD::SetControlsVisible(bool bVisible)
{
    bControlsVisible = bVisible;
}

void AAshWellIntroHUD::SetIntroProgress(float ElapsedSeconds)
{
    ProgressOverride = ElapsedSeconds;
}

void AAshWellIntroHUD::DrawCaption(const FString& Text, const FVector2D& Position,
    float FontSize, const FLinearColor& Color, bool bCentered)
{
    if (!Canvas || Text.IsEmpty() || Color.A <= 0.001f)
    {
        return;
    }

    InitializeFont();
    const UFont* Font = FontOverride ? FontOverride.Get() : RuntimeCaptionFont.Get();
    const FSlateFontInfo FontInfo(Font, FontSize, FName(TEXT("Regular")));

    FCanvasTextItem Item(Position, FText::FromString(Text), FontInfo, Color);
    Item.bCentreX = bCentered;
    Item.EnableShadow(FLinearColor(0.0f, 0.0f, 0.0f, Color.A * 0.85f), FVector2D(1.0f, 2.0f));
    Canvas->DrawItem(Item);
    LastDrawnCaption = Text;
    LastDrawnSize = Item.DrawnSize;
}

void AAshWellIntroHUD::DrawHUD()
{
    Super::DrawHUD();
    ++DrawHUDCount;
    if (WorldTime() - LastSnapshotTime >= 1.0)
    {
        LastSnapshotTime = WorldTime();
        WriteRuntimeSnapshot();
    }
    if (!Canvas || !bShowHUD)
    {
        return;
    }

    const float Width = Canvas->ClipX;
    const float Height = Canvas->ClipY;
    const float Scale = FMath::Clamp(FMath::Min(Width / 1920.0f, Height / 1080.0f), 0.65f, 1.6f);
    const auto* DebugPlayer=Cast<AAshWellCombatCharacter>(GetOwningPawn());
    if (UGameplayStatics::IsGamePaused(this)&&!(DebugPlayer&&DebugPlayer->IsMountedDebugPauseActive()))
    {
        DrawRect(FLinearColor(.015,.019,.022,.88),0,0,Width,Height);
        DrawCaption(TEXT("检修站  /  暂停"),FVector2D(Width*.5,Height*.28),28*Scale,FLinearColor(.87,.81,.68,1),true);
        if(auto* S=Cast<UAshWellSession>(GetGameInstance()))
        {
            auto* PC=Cast<AAshWellIntroPlayerController>(GetOwningPlayerController());
            const int32 Selected=PC?PC->GetSettingsRow():0;
            const FString Rows[]={FString::Printf(TEXT("主音量   %d%%"),FMath::RoundToInt(S->MasterVolume*100)),
                FString::Printf(TEXT("鼠标灵敏度   %.1f"),S->MouseSensitivity),S->bSubtitles?TEXT("对白字幕   开启"):TEXT("对白字幕   关闭")};
            for(int32 I=0;I<3;++I)DrawCaption((Selected==I?TEXT("›  "):TEXT("   "))+Rows[I],FVector2D(Width*.5,Height*.40+I*46*Scale),20*Scale,Selected==I?FLinearColor(1,.68,.30,1):FLinearColor(.67,.69,.68,1),true);
        }
        DrawCaption(TEXT("↑ ↓ 选择    ← → 调整    Esc 继续"),FVector2D(Width*.5,Height*.68),16*Scale,FLinearColor(.8,.8,.75,1),true);
        DrawCaption(TEXT("R 重新挑战    F10 退出游戏"),FVector2D(Width*.5,Height*.74),14*Scale,FLinearColor(.6,.62,.61,1),true);
        return;
    }

    if(AAshWellCombatCharacter* Combat=Cast<AAshWellCombatCharacter>(GetOwningPawn()))
    {
        DrawCombatHUD(Combat);
        return;
    }
    const float Elapsed = ProgressOverride >= 0.0f
        ? ProgressOverride : static_cast<float>(WorldTime() - IntroStartTime);

    const float TitleAlpha = CaptionEnvelope(Elapsed, 5.5f, 1.2f, 2.0f);
    DrawCaption(TEXT("第一眼深井"), FVector2D(Width * 0.5f, Height * 0.16f),
        26.0f * Scale, FLinearColor(0.85f, 0.83f, 0.75f, TitleAlpha * 0.88f), true);

    if (bControlsVisible)
    {
        const float ControlsAlpha = CaptionEnvelope(Elapsed - 1.0f, 8.5f, 1.0f, 2.0f);
        DrawCaption(TEXT("W A S D 行走   ·   鼠标环顾"),
            FVector2D(42.0f * Scale, Height - 56.0f * Scale), 12.0f * Scale,
            FLinearColor(0.79f, 0.79f, 0.74f, ControlsAlpha * 0.7f), false);
    }

    if (!Subtitle.IsEmpty())
    {
        const float SubtitleElapsed = static_cast<float>(WorldTime() - SubtitleStartTime);
        const float SubtitleAlpha = CaptionEnvelope(SubtitleElapsed, SubtitleDuration, 0.2f, 0.5f);
        DrawCaption(Subtitle, FVector2D(Width * 0.5f, Height - 120.0f * Scale),
            17.0f * Scale, FLinearColor(0.94f, 0.92f, 0.85f, SubtitleAlpha), true);
    }

    if (bShowFocusDot)
    {
        const float Size = 1.5f * Scale;
        DrawRect(FLinearColor(0.82f, 0.81f, 0.75f, 0.25f),
            Width * 0.5f - Size * 0.5f, Height * 0.5f - Size * 0.5f, Size, Size);
    }
}

void AAshWellIntroHUD::DrawCombatHUD(AAshWellCombatCharacter* Player)
{
    const float Width=Canvas->ClipX,Height=Canvas->ClipY;
    const float Scale=FMath::Clamp(Height/900.f,.65f,1.6f);
    const FLinearColor Ink(.86f,.84f,.77f,1);
    const float X=42*Scale,Y=40*Scale;
    auto Bar=[&](float BX,float BY,float BW,float BH,float Fraction,const FLinearColor& Color)
    {
        DrawRect(FLinearColor(.02f,.022f,.025f,.85f),BX-2,BY-2,BW+4,BH+4);
        DrawRect(FLinearColor(.12f,.12f,.11f,.8f),BX,BY,BW,BH);
        DrawRect(Color,BX,BY,BW*FMath::Clamp(Fraction,0.f,1.f),BH);
    };
    DrawCaption(TEXT("生命"),FVector2D(X,Y),12*Scale,Ink,false);
    Bar(X+44*Scale,Y+4*Scale,225*Scale,10*Scale,Player->GetHealthFraction(),FLinearColor(.48f,.085f,.06f,.95f));
    DrawCaption(TEXT("体力"),FVector2D(X,Y+25*Scale),12*Scale,Ink,false);
    Bar(X+44*Scale,Y+29*Scale,225*Scale,7*Scale,Player->GetStaminaFraction(),FLinearColor(.35f,.43f,.24f,.95f));
    auto* Chapter=AAshWellChapterDirector::Find(GetWorld());
    DrawCaption(Player->IsMountedExperiment()?TEXT("骑卫试炼 / 黄昏庭院"):Chapter?Chapter->Zone():TEXT("灰烬深井 / 检修站"),FVector2D(Width-170*Scale,40*Scale),14*Scale,Ink,true);
    DrawCaption(TEXT("WASD 跑动 · Ctrl 慢走   ·   空格 跳跃 · Shift 点按闪避/按住冲刺   ·   左键 横斩 · 右键 重击   ·   Tab 锁定   ·   R 重来"),
        FVector2D(Width*.5f,Height-32*Scale),12*Scale,FLinearColor(.8f,.79f,.74f,.78f),true);
    DrawCaption(Player->GetPrompt(),FVector2D(Width*.5f,Height-76*Scale),16*Scale,Ink,true);
    auto* Session=Cast<UAshWellSession>(GetGameInstance());
    if(!Session||Session->bSubtitles)DrawCaption(Player->GetStorySubtitle(),FVector2D(Width*.5f,Height*.73f),20*Scale,Ink,true);
    if(Player->IsRecordVisible())
    {
        DrawRect(FLinearColor(.016,.020,.025,.94),Width*.20,Height*.24,Width*.60,Height*.35);
        DrawCaption(TEXT("服役记录 · 井下维护 / 07"),FVector2D(Width*.5,Height*.29),23*Scale,FLinearColor(.85,.68,.43,1),true);
        DrawCaption(TEXT("原岗位：升降机检修工    状态：强制服役"),FVector2D(Width*.5,Height*.37),18*Scale,Ink,true);
        DrawCaption(TEXT("终止申请：驳回    原因：替代人员尚未到岗"),FVector2D(Width*.5,Height*.43),18*Scale,Ink,true);
        DrawCaption(TEXT("警告：断电后残存意识可能恢复。禁止擅自停机。"),FVector2D(Width*.5,Height*.51),17*Scale,FLinearColor(.76,.47,.36,1),true);
    }
    AAshWellWarden* Enemy=Player->GetWarden();
    if(!Player->IsMountedExperiment()&&!Player->HasPower()&&(!Chapter||Chapter->IsAtStation()))
    {
        FVector2D Marker;
        if(GetOwningPlayerController()->ProjectWorldLocationToScreen((Player->IsEntryClosed()?Player->GetEntryPoint():Player->GetConsolePoint())+FVector(0,0,75),Marker))
        {
            Marker.X=FMath::Clamp(Marker.X,100.0,static_cast<double>(Width)-100.0);
            Marker.Y=FMath::Clamp(Marker.Y,120.0,static_cast<double>(Height)-185.0);
            DrawCaption(Player->IsEntryClosed()?TEXT("开启铁门  [E]"):TEXT("供电闸  [E]"),Marker,15*Scale,FLinearColor(.94f,.71f,.36f,1),true);
        }
    }
    if(Player->GetCombatEnemy()&&Player->IsEncounterActive()&&!Player->HasWon())
    {
        const float BW=Width*.46f;
        DrawCaption(Player->GetCombatEnemyName(),FVector2D(Width*.5f,Height-172*Scale),16*Scale,Ink,true);
        Bar((Width-BW)*.5f,Height-130*Scale,BW,9*Scale,Player->GetCombatEnemyHealthFraction(),FLinearColor(.45f,.075f,.045f,.95f));
        if(Player->IsLockedOn())
        {
            FVector2D Screen;
            if(GetOwningPlayerController()->ProjectWorldLocationToScreen(Player->GetCombatAimPoint(),Screen))
            {
                const float R=5*Scale;
                DrawLine(Screen.X-R,Screen.Y,Screen.X,Screen.Y-R,Ink,1.5f);
                DrawLine(Screen.X,Screen.Y-R,Screen.X+R,Screen.Y,Ink,1.5f);
                DrawLine(Screen.X+R,Screen.Y,Screen.X,Screen.Y+R,Ink,1.5f);
                DrawLine(Screen.X,Screen.Y+R,Screen.X-R,Screen.Y,Ink,1.5f);
            }
        }
    }
    if(Player->GetDamageFlash()>0)
    {
        const FLinearColor Red(.35f,.012f,.008f,Player->GetDamageFlash()*.4f);
        DrawRect(Red,0,0,Width,18*Scale);DrawRect(Red,0,Height-18*Scale,Width,18*Scale);
        DrawRect(Red,0,0,18*Scale,Height);DrawRect(Red,Width-18*Scale,0,18*Scale,Height);
    }
    if(Player->IsDead()||(Player->HasWon()&&Player->GetEndingTime()<2.f))
    {
        DrawRect(FLinearColor(.015f,.017f,.02f,.55f),0,Height*.40f,Width,Height*.15f);
        DrawCaption(Player->IsDead()?TEXT("你倒下了"):Player->IsMountedExperiment()?TEXT("骑卫已倒下"):TEXT("守井者已停机"),FVector2D(Width*.5f,Height*.445f),30*Scale,
            Player->IsDead()?FLinearColor(.63f,.18f,.12f,1):FLinearColor(.78f,.66f,.40f,1),true);
    }
    if(Player->IsMountedExperiment()&&Player->IsMountedDebugEnabled())
    {
        if(!Player->IsMountedDebugVisible())DrawCaption(TEXT("F1 战斗调试"),FVector2D(42*Scale,102*Scale),12*Scale,FLinearColor(.68,.72,.65,.8),false);
        else
        {
            const TArray<FString> Lines=Player->GetMountedDebugLines();
            const float PX=32*Scale,PY=102*Scale,PW=FMath::Min(650*Scale,Width-64*Scale),PH=(54+24*Lines.Num())*Scale;
            DrawRect(FLinearColor(.018,.024,.024,.94),PX,PY,PW,PH);
            DrawRect(FLinearColor(.48,.57,.37,.90),PX,PY,3*Scale,PH);
            DrawCaption(TEXT("骑卫战斗调试"),FVector2D(PX+15*Scale,PY+12*Scale),17*Scale,FLinearColor(.87,.86,.70,1),false);
            for(int32 I=0;I<Lines.Num();++I)
                DrawCaption(Lines[I],FVector2D(PX+15*Scale,PY+(43+24*I)*Scale),13.5f*Scale,I==2?FLinearColor(.94,.72,.40,1):FLinearColor(.79,.83,.78,1),false);
        }
    }
}

void AAshWellIntroHUD::WriteRuntimeSnapshot() const
{
    if (!GetWorld() || !GetWorld()->IsGameWorld())
    {
        return;
    }
    TSharedRef<FJsonObject> Snapshot = MakeShared<FJsonObject>();
    Snapshot->SetBoolField(TEXT("begin_play_called"), bBeginPlayCalled);
    Snapshot->SetNumberField(TEXT("draw_hud_count"), static_cast<double>(DrawHUDCount));
    Snapshot->SetBoolField(TEXT("show_hud"), bShowHUD);
    Snapshot->SetBoolField(TEXT("canvas_valid"), Canvas != nullptr);
    Snapshot->SetNumberField(TEXT("canvas_width"), Canvas ? Canvas->ClipX : 0.0);
    Snapshot->SetNumberField(TEXT("canvas_height"), Canvas ? Canvas->ClipY : 0.0);
    Snapshot->SetStringField(TEXT("subtitle"), Subtitle);
    Snapshot->SetNumberField(TEXT("world_time"), WorldTime());
    Snapshot->SetNumberField(TEXT("intro_elapsed"), WorldTime() - IntroStartTime);
    Snapshot->SetNumberField(TEXT("subtitle_elapsed"), WorldTime() - SubtitleStartTime);
    Snapshot->SetNumberField(TEXT("subtitle_duration"), SubtitleDuration);
    Snapshot->SetNumberField(TEXT("progress_override"), ProgressOverride);
    Snapshot->SetStringField(TEXT("font_path"), FontPath);
    Snapshot->SetBoolField(TEXT("runtime_font_valid"), RuntimeCaptionFont != nullptr);
    Snapshot->SetStringField(TEXT("last_drawn_caption"), LastDrawnCaption);
    Snapshot->SetNumberField(TEXT("last_drawn_width"), LastDrawnSize.X);
    Snapshot->SetNumberField(TEXT("last_drawn_height"), LastDrawnSize.Y);

    FString Serialized;
    const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Serialized);
    FJsonSerializer::Serialize(Snapshot, Writer);
    const FString Directory = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Automation"));
    IFileManager::Get().MakeDirectory(*Directory, true);
    const FString File = FPaths::Combine(Directory, TEXT("intro-hud-runtime.json"));
    const FString TemporaryFile = File + TEXT(".tmp");
    if (FFileHelper::SaveStringToFile(Serialized, *TemporaryFile, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
    {
        IFileManager::Get().Move(*File, *TemporaryFile, true, true, false, true);
    }
}
