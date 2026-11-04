import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Dialogs

ApplicationWindow {
    id: window
    width: 1440; height: 940
    minimumWidth: 1100; minimumHeight: 760
    visible: true
    title: "VEX · Local Video Studio"
    color: "#0d0e16"
    palette.window: "#0d0e16"
    palette.windowText: "#ebeaf6"
    palette.base: "#141622"
    palette.text: "#ebeaf6"
    palette.button: "#26243c"
    palette.buttonText: "#ebeaf6"
    palette.highlight: "#9170ed"
    palette.highlightedText: "#ffffff"
    font.family: "Segoe UI"
    font.pixelSize: 14
    property int page: 0
    property int sceneIndex: 0

    function syncDraft() {
        backend.updateDraft(titleField.text, storyField.text, aspect.currentText,
                            parseInt(resolution.currentText), parseInt(fps.currentText))
    }
    function refresh() {
        titleField.text = backend.title
        storyField.text = backend.story
        jsonEditor.text = backend.projectJson
        const data = JSON.parse(backend.projectJson)
        aspect.currentIndex = ["16:9","9:16","1:1"].indexOf(data.export.aspect)
        resolution.currentIndex = [480,720,1080,1440,2160].indexOf(data.export.resolution)
        fps.currentIndex = [24,30,60].indexOf(data.export.fps)
    }
    Component.onCompleted: { lastProject = backend.projectJson; refresh(); settingsEditor.text = backend.settingsJson }
    Connections {
        target: backend
        function onChanged() {
            if (window.lastSettings !== backend.settingsJson) {
                window.lastSettings = backend.settingsJson
                settingsEditor.text = backend.settingsJson
            }
            // Refresh text only when persisted data actually changes; keep uncommitted edits.
            if (window.lastProject !== backend.projectJson) {
                window.lastProject = backend.projectJson
                window.refresh()
            }
        }
    }
    property string lastProject: ""
    property string lastSettings: ""

    component VexButton: Button {
        id: control
        implicitHeight: 40
        implicitWidth: Math.max(88, textItem.implicitWidth + 28)
        contentItem: Text {
            id: textItem
            text: control.text
            color: control.enabled ? "#eeeafa" : "#666780"
            font: control.font
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            radius: 7
            color: !control.enabled ? "#222331" : control.down ? "#6d4dba" : control.highlighted ? "#8a61df" : control.hovered ? "#35304c" : "#25233a"
            border.color: control.highlighted ? "#9d7be7" : "#353047"
            border.width: 1
        }
    }

    FileDialog {
        id: openDialog
        title: "VEX proje dosyası aç"
        nameFilters: ["VEX project (project.json *.json)"]
        onAccepted: backend.openProject(selectedFile.toString())
    }

    RowLayout {
        anchors.fill: parent; spacing: 0
        Rectangle {
            Layout.preferredWidth: 218; Layout.fillHeight: true; color: "#11121c"
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 22; spacing: 12
                Label { text: "VEX"; font.pixelSize: 37; font.bold: true; color: "#b298ff" }
                Label { text: "LOCAL VIDEO STUDIO"; font.pixelSize: 10; font.letterSpacing: 2; color: "#777b99" }
                Item { Layout.preferredHeight: 24 }
                Repeater {
                    model: ["Story Studio", "Scene Director", "Projeler", "Render geçmişi", "Ayarlar", "Asset Library"]
                    VexButton {
                        required property string modelData
                        required property int index
                        text: modelData
                        Layout.fillWidth: true; Layout.preferredHeight: 43
                        highlighted: window.page === index
                        onClicked: { window.page = index; if (index === 4) settingsEditor.text = backend.settingsJson }
                    }
                }
                Item { Layout.fillHeight: true }
                Rectangle { Layout.fillWidth: true; height: 1; color: "#292a3d" }
                Label { text: "●  Yerel çalışma"; color: "#85d9bd"; font.pixelSize: 12 }
                Label { text: "Prosedürel 2D + Motion\nKokoro / Whisper · English\nv0.1 · geliştirme sürümü"; color: "#777b99"; font.pixelSize: 11; lineHeight: 1.5 }
            }
        }
        ColumnLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; Layout.margins: 26; spacing: 16
            RowLayout {
                ColumnLayout {
                    Label { text: ["Hikâyeni harekete geçir.", "Sahneyi yönet.", "Projelerin", "Render geçmişi", "Yerel motor ayarları", "Tekrar kullanılabilir geometri"][window.page]; font.pixelSize: 27; font.bold: true }
                    Label { text: "Yerel AI planlar. VEX geometriyi çizer."; color: "#8b8fa9"; font.pixelSize: 13 }
                }
                Item { Layout.fillWidth: true }
                VexButton { text: "Yeni proje"; enabled: !backend.busy; onClicked: backend.newProject() }
                VexButton { text: "Proje aç"; enabled: !backend.busy; onClicked: openDialog.open() }
                VexButton { text: "Kaydet"; enabled: !backend.busy; highlighted: true; onClicked: { window.syncDraft(); backend.saveProject() } }
            }

            StackLayout {
                currentIndex: window.page
                Layout.fillWidth: true; Layout.fillHeight: true

                RowLayout {
                    spacing: 20
                    Rectangle {
                        Layout.preferredWidth: 390; Layout.fillHeight: true
                        color: "#161824"; radius: 14
                        ScrollView {
                            anchors.fill: parent; anchors.margins: 22
                            contentWidth: availableWidth
                            ColumnLayout {
                                width: parent.width; spacing: 14; enabled: !backend.busy
                                Label { text: "01  /  HİKÂYE"; color: "#b298ff"; font.bold: true; font.pixelSize: 12 }
                                TextField { id: titleField; objectName: "titleField"; placeholderText: "Video başlığı"; Layout.fillWidth: true; maximumLength: 200 }
                                ScrollView {
                                    Layout.fillWidth: true; Layout.preferredHeight: 205
                                    TextArea { color: "#ebeaf6"; placeholderTextColor: "#797e99"; id: storyField; objectName: "storyField"; placeholderText: "Bir hikâye yaz…\nYerel LLM, hikâyeni çizilebilir sahnelere ayırsın."; wrapMode: TextEdit.Wrap; selectByMouse: true }
                                }
                                Label { text: "02  /  VİDEO AYARLARI"; color: "#b298ff"; font.bold: true; font.pixelSize: 12 }
                                RowLayout {
                                    ComboBox { id: aspect; model: ["16:9", "9:16", "1:1"]; Layout.fillWidth: true }
                                    ComboBox { id: resolution; model: ["480", "720", "1080", "1440", "2160"]; currentIndex: 1; Layout.fillWidth: true }
                                    ComboBox { id: fps; model: ["24", "30", "60"]; Layout.fillWidth: true }
                                }
                                VexButton { text: "Yerel LLM ile sahneleri planla"; Layout.fillWidth: true; highlighted: true; onClicked: { window.syncDraft(); backend.plan() } }
                                VexButton { text: "Hikâyeden sesli MP4 üret"; Layout.fillWidth: true; onClicked: { window.syncDraft(); backend.generate() } }
                                Label { text: "llama-server ve GGUF dosyaları Ayarlar'da seçilmelidir."; wrapMode: Text.WordWrap; Layout.fillWidth: true; color: "#858ba5"; font.pixelSize: 11 }
                                Rectangle { Layout.fillWidth: true; height: 1; color: "#2a2d42" }
                                VexButton { text: "Prosedürel robot örneğini aç"; Layout.fillWidth: true; onClicked: backend.loadExample() }
                                Label { text: "Örnek, elle hazırlanmış üç sahnedir. Model olmadan gerçek çizim ve sessiz MP4 testi yapabilirsiniz."; wrapMode: Text.WordWrap; Layout.fillWidth: true; color: "#858ba5"; font.pixelSize: 11 }
                            }
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true; Layout.fillHeight: true; spacing: 12
                        Rectangle {
                            Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumHeight: 220; color: "#171a2a"; radius: 14
                            Image { anchors.fill: parent; anchors.margins: 10; source: backend.previewUrl; fillMode: Image.PreserveAspectFit; cache: false }
                            Column {
                                anchors.centerIn: parent; spacing: 12; visible: backend.previewUrl === ""
                                Label { anchors.horizontalCenter: parent.horizontalCenter; text: "Sahnen burada canlanacak"; font.pixelSize: 21; color: "#9c94bd" }
                                Label { anchors.horizontalCenter: parent.horizontalCenter; text: "Bir sahne planla veya robot örneğini aç."; color: "#6f7693" }
                            }
                            Label { anchors.top: parent.top; anchors.left: parent.left; anchors.margins: 18; text: "360p ÖNİZLEME"; color: "#a3a7bd"; font.pixelSize: 10 }
                        }
                        RowLayout {
                            ComboBox {
                                id: scenePicker; Layout.fillWidth: true; model: backend.scenes; textRole: "title"
                                onActivated: { window.sceneIndex = currentIndex; backend.preview(currentIndex, scrub.value) }
                            }
                            Slider { id: scrub; from: 0; to: backend.scenes.length > window.sceneIndex ? backend.scenes[window.sceneIndex].duration : 1; onMoved: backend.preview(scenePicker.currentIndex, value); Layout.preferredWidth: 180 }
                            Label { text: scrub.value.toFixed(1) + " s"; color: "#9a9eb7" }
                        }
                        CheckBox { id: withVoice; text: "Kokoro İngilizce ses + Whisper altyazı ekle"; enabled: !backend.busy }
                        Label { text: backend.planningWarnings; visible: text !== ""; color: "#d8ba7a"; font.pixelSize: 11; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                        Label { text: withVoice.checked ? "Gerçek yerel ses ve Whisper modelleri gerekir. MP4 seçilebilir altyazı içerir." : "Sessiz render · ses veya altyazı üretilmez."; color: "#858ba5"; font.pixelSize: 11; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                        RowLayout {
                            VexButton { text: "360p video önizle"; enabled: !backend.busy && backend.scenes.length > 0; onClicked: { window.syncDraft(); backend.renderVideo(true, withVoice.checked) } }
                            VexButton { text: "MP4 dışa aktar"; highlighted: true; enabled: !backend.busy && backend.scenes.length > 0; onClicked: { window.syncDraft(); backend.renderVideo(false, withVoice.checked) } }
                            VexButton { text: "Videoyu aç"; enabled: backend.outputPath !== ""; onClicked: backend.openOutput() }
                        }
                    }
                }

                ColumnLayout {
                    Label { text: "Doğrulanan sahne DSL · JSON"; font.pixelSize: 19; font.bold: true }
                    Label { text: "Nesne, animasyon, kamera ve narration alanlarını düzenle. Desteklenmeyen komutlar reddedilir."; color: "#8b8fa9" }
                    ScrollView {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        TextArea { color: "#ebeaf6"; placeholderTextColor: "#797e99"; id: jsonEditor; font.family: "Consolas"; font.pixelSize: 13; selectByMouse: true; wrapMode: TextEdit.NoWrap; readOnly: backend.busy }
                    }
                    VexButton { text: "JSON'u doğrula ve kaydet"; highlighted: true; enabled: !backend.busy; onClicked: backend.applyJson(jsonEditor.text) }
                }

                ScrollView {
                    Layout.fillWidth: true; Layout.fillHeight: true; contentWidth: availableWidth
                    ColumnLayout {
                        width: parent.width; spacing: 12
                        Label { text: backend.recent.length ? "Son kaydedilen projeler" : "Henüz kayıtlı proje yok."; font.pixelSize: 18 }
                        Repeater {
                            model: backend.recent
                            Frame {
                                required property var modelData
                                Layout.fillWidth: true
                                RowLayout {
                                    anchors.fill: parent
                                    ColumnLayout {
                                        Label { text: modelData.title; font.bold: true }
                                        Label { text: modelData.path; color: "#8b8fa9"; font.pixelSize: 11; elide: Text.ElideMiddle; Layout.maximumWidth: 680 }
                                    }
                                    Item { Layout.fillWidth: true }
                                    VexButton { text: "Aç"; enabled: !backend.busy; onClicked: { backend.openProject(modelData.path); window.page = 0 } }
                                }
                            }
                        }
                    }
                }

                ScrollView {
                    Layout.fillWidth: true; Layout.fillHeight: true; contentWidth: availableWidth
                    ColumnLayout {
                        width: parent.width; spacing: 12
                        Label { text: "Gerçek görev kayıtları"; font.pixelSize: 18 }
                        Repeater {
                            model: backend.history
                            Frame {
                                required property var modelData
                                Layout.fillWidth: true
                                ColumnLayout {
                                    width: parent.width
                                    Label { text: modelData.status + " · " + modelData.kind; color: modelData.status === "COMPLETED" ? "#85d9bd" : "#b298ff" }
                                    ProgressBar { value: modelData.progress; Layout.fillWidth: true }
                                    Label { text: modelData.error; visible: text !== ""; color: "#eea0a9"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                                }
                            }
                        }
                    }
                }

                ColumnLayout {
                    Label { text: "Runtime yolları ve yerel ayarlar"; font.pixelSize: 19; font.bold: true }
                    Label { text: "Windows yollarında / veya çift \\ kullanın. gpu_layers: 0 CPU, pozitif değer GPU katmanlarıdır.\nSes için [audio] bağımlılıkları gerekir. Modeller otomatik indirilmez."; color: "#8b8fa9"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    ScrollView {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        TextArea { color: "#ebeaf6"; placeholderTextColor: "#797e99"; id: settingsEditor; font.family: "Consolas"; font.pixelSize: 14; selectByMouse: true; readOnly: backend.busy }
                    }
                    RowLayout {
                        VexButton { text: "Ayarları kaydet"; enabled: !backend.busy; highlighted: true; onClicked: backend.saveSettings(settingsEditor.text) }
                        VexButton { text: "Runtime durumunu denetle"; enabled: !backend.busy; onClicked: backend.checkRuntime() }
                        VexButton { text: "Temel modelleri indir (~1.6 GB)"; enabled: !backend.busy; onClicked: backend.prepareModels() }
                        VexButton { text: "Veri klasörünü aç"; onClicked: backend.openFolder() }
                    }
                }

                ColumnLayout {
                    Label { text: "Sahne geometrisini sürümlü asset olarak sakla"; font.pixelSize: 18 }
                    RowLayout {
                        ComboBox { id: assetScene; model: backend.scenes; textRole: "title"; Layout.preferredWidth: 300 }
                        TextField { id: assetName; placeholderText: "Asset adı"; Layout.fillWidth: true }
                        VexButton { text: "Kütüphaneye kaydet"; enabled: !backend.busy; onClicked: backend.saveAsset(assetScene.currentIndex, assetName.text) }
                    }
                    Label { text: "Kaydedilen sürümler değişmez. Ekleme, nesne kimliklerini ayırır ve görünümü korur."; color: "#8b8fa9" }
                    ScrollView {
                        Layout.fillWidth: true; Layout.fillHeight: true; contentWidth: availableWidth
                        ColumnLayout {
                            width: parent.width
                            Repeater {
                                model: backend.assets
                                Frame {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    RowLayout {
                                        anchors.fill: parent
                                        Label { text: modelData.name + " · v" + modelData.version + " · " + modelData.count + " nesne" }
                                        Item { Layout.fillWidth: true }
                                        VexButton { text: "Seçili sahneye ekle"; enabled: !backend.busy; onClicked: backend.insertAsset(modelData.key, assetScene.currentIndex) }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 112; color: "#161824"; radius: 12
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 14; spacing: 7
                    RowLayout {
                        Label { text: backend.busy ? "İŞLENİYOR" : "DURUM"; color: "#b298ff"; font.pixelSize: 10; font.bold: true }
                        Item { Layout.fillWidth: true }
                        Label { text: Math.round(backend.progress * 100) + "%"; color: "#b5b6c9" }
                        VexButton { text: "İptal"; visible: backend.busy; onClicked: backend.cancel() }
                    }
                    ProgressBar { Layout.fillWidth: true; value: backend.progress }
                    ScrollView {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        TextArea { color: "#ebeaf6"; placeholderTextColor: "#797e99"; text: backend.message; readOnly: true; selectByMouse: true; wrapMode: TextEdit.Wrap; font.pixelSize: 11; padding: 0; background: null }
                    }
                }
            }
        }
    }
}
