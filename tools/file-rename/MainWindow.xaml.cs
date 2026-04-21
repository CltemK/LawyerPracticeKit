using System;
using System.IO;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;

namespace LegalFileRenamer
{
    public partial class MainWindow : Window
    {
        private readonly string _originalFilePath;
        private readonly string _originalFileName;
        private readonly string _extension;
        private bool _isLawyerFile;
        private bool _initialized;

        public MainWindow(string filePath)
        {
            InitializeComponent();

            _originalFilePath = filePath;
            _originalFileName = Path.GetFileNameWithoutExtension(filePath);
            _extension = Path.GetExtension(filePath);

            Loaded += MainWindow_Loaded;
            SetupEventHandlers();
        }

        private void MainWindow_Loaded(object sender, RoutedEventArgs e)
        {
            OriginalPathTextBox.Text = _originalFilePath;
            DateTextBox.Text = DateTime.Now.ToString("yyyyMMdd");
            FileNameTextBox.Text = _originalFileName;

            if (TryParseLawyerFileName(_originalFileName, out var date, out var typeTag, out var name, out var version))
            {
                _isLawyerFile = true;

                DateTextBox.Text = date;
                FileNameTextBox.Text = name;

                if (!string.IsNullOrEmpty(version))
                {
                    var v = version;
                    if (v.StartsWith("V", StringComparison.OrdinalIgnoreCase))
                        v = v.Substring(1);
                    VersionTextBox.Text = v;
                }

                if (typeTag == "【客户】")
                {
                    CategoryClientRadio.IsChecked = true;
                }
                else
                {
                    CategoryLawyerRadio.IsChecked = true;
                    if (typeTag == "【初稿】")
                        SubTypeDraftRadio.IsChecked = true;
                    else if (typeTag.StartsWith("【修订"))
                        SubTypeRevisionRadio.IsChecked = true;
                    else if (typeTag == "【终稿】")
                        SubTypeFinalRadio.IsChecked = true;
                }

                // Show finalize bar for drafts/revisions (not 客户, not 终稿)
                if (typeTag != "【客户】" && typeTag != "【终稿】")
                    FinalizeBar.Visibility = Visibility.Visible;
            }
            else
            {
                CategoryClientRadio.IsChecked = true;
            }

            _initialized = true;
            UpdatePreview();
        }

        private void SetupEventHandlers()
        {
            DateTextBox.TextChanged += (s, e) => UpdatePreview();
            FileNameTextBox.TextChanged += (s, e) => UpdatePreview();
            VersionTextBox.TextChanged += (s, e) => UpdatePreview();
        }

        private void CategoryRadio_Checked(object sender, RoutedEventArgs e)
        {
            if (!_initialized) return;

            if (CategoryLawyerRadio.IsChecked == true)
            {
                LawyerSubTypePanel.Visibility = Visibility.Visible;
                if (SubTypeDraftRadio.IsChecked != true &&
                    SubTypeRevisionRadio.IsChecked != true &&
                    SubTypeFinalRadio.IsChecked != true)
                {
                    SubTypeDraftRadio.IsChecked = true;
                }
            }
            else
            {
                LawyerSubTypePanel.Visibility = Visibility.Collapsed;
            }

            UpdateFinalizeBarVisibility();
            UpdatePreview();
        }

        private void SubTypeRadio_Checked(object sender, RoutedEventArgs e)
        {
            if (!_initialized) return;
            UpdateFinalizeBarVisibility();
            UpdatePreview();
        }

        private void UpdateFinalizeBarVisibility()
        {
            if (!_isLawyerFile)
            {
                FinalizeBar.Visibility = Visibility.Collapsed;
                return;
            }

            FinalizeBar.Visibility =
                (CategoryLawyerRadio.IsChecked == true && SubTypeFinalRadio.IsChecked != true)
                    ? Visibility.Visible
                    : Visibility.Collapsed;
        }

        private string FormatVersion(string rawVersion)
        {
            if (string.IsNullOrEmpty(rawVersion)) return "";
            var v = rawVersion.Trim();
            if (v.StartsWith("V", StringComparison.OrdinalIgnoreCase))
                v = v.Substring(1);
            if (string.IsNullOrEmpty(v)) return "";
            return "V" + v;
        }

        private string GetFileTypeTag()
        {
            if (CategoryClientRadio.IsChecked == true)
                return "【客户】";

            if (SubTypeDraftRadio.IsChecked == true)
                return "【初稿】";
            if (SubTypeRevisionRadio.IsChecked == true)
            {
                var version = FormatVersion(VersionTextBox.Text);
                if (!string.IsNullOrEmpty(version))
                    return $"【修订{version}】";
                return "【修订V1】";
            }
            if (SubTypeFinalRadio.IsChecked == true)
                return "【终稿】";

            return "";
        }

        private void UpdatePreview()
        {
            var date = DateTextBox.Text.Trim();
            var fileType = GetFileTypeTag();
            var fileName = FileNameTextBox.Text.Trim();
            var version = FormatVersion(VersionTextBox.Text.Trim());

            if (string.IsNullOrEmpty(date) && string.IsNullOrEmpty(fileType) &&
                string.IsNullOrEmpty(fileName) && string.IsNullOrEmpty(version))
            {
                PreviewTextBlock.Text = _originalFileName + _extension;
                return;
            }

            string newFileName;
            if (string.IsNullOrEmpty(version))
            {
                newFileName = $"{date}_{fileType}_{fileName}{_extension}";
            }
            else
            {
                newFileName = $"{date}_{fileType}_{fileName}_{version}{_extension}";
            }
            PreviewTextBlock.Text = newFileName;
        }

        private bool ValidateInputs()
        {
            ErrorTextBlock.Text = "";

            var date = DateTextBox.Text.Trim();
            if (string.IsNullOrEmpty(date))
            {
                ErrorTextBlock.Text = "日期不能为空";
                return false;
            }

            if (!Regex.IsMatch(date, @"^\d{8}$"))
            {
                ErrorTextBlock.Text = "日期格式错误，请输入8位数字（如 20260418）";
                return false;
            }

            var year = int.Parse(date.Substring(0, 4));
            var month = int.Parse(date.Substring(4, 2));
            var day = int.Parse(date.Substring(6, 2));

            if (year < 1900 || year > 2100)
            {
                ErrorTextBlock.Text = "年份必须在1900-2100之间";
                return false;
            }

            if (month < 1 || month > 12)
            {
                ErrorTextBlock.Text = "月份必须在01-12之间";
                return false;
            }

            if (day < 1 || day > 31)
            {
                ErrorTextBlock.Text = "日期必须在01-31之间";
                return false;
            }

            var fileName = FileNameTextBox.Text.Trim();
            if (string.IsNullOrEmpty(fileName))
            {
                ErrorTextBlock.Text = "文件名称不能为空";
                return false;
            }

            var version = VersionTextBox.Text.Trim();
            if (!string.IsNullOrEmpty(version) && !Regex.IsMatch(version, @"^V?\d+(\.\d+)?$", RegexOptions.IgnoreCase))
            {
                ErrorTextBlock.Text = "版本号格式错误，只需输入数字（如 1、1.1）";
                return false;
            }

            return true;
        }

        private void ConfirmButton_Click(object sender, RoutedEventArgs e)
        {
            if (!ValidateInputs())
                return;

            try
            {
                var directory = Path.GetDirectoryName(_originalFilePath);
                var newFileName = PreviewTextBlock.Text;
                var newFilePath = Path.Combine(directory!, newFileName);

                if (File.Exists(newFilePath) &&
                    !string.Equals(newFilePath, _originalFilePath, StringComparison.OrdinalIgnoreCase))
                {
                    var result = MessageBox.Show(
                        $"文件 {newFileName} 已存在，是否覆盖？",
                        "确认",
                        MessageBoxButton.YesNo,
                        MessageBoxImage.Warning);

                    if (result != MessageBoxResult.Yes)
                        return;

                    File.Move(_originalFilePath, newFilePath, overwrite: true);
                }
                else
                {
                    File.Move(_originalFilePath, newFilePath);
                }

                MessageBox.Show(
                    $"重命名成功！\n新文件名：{newFileName}",
                    "成功",
                    MessageBoxButton.OK,
                    MessageBoxImage.Information);

                DialogResult = true;
                Close();
            }
            catch (Exception ex)
            {
                ErrorTextBlock.Text = $"重命名失败：{ex.Message}";
            }
        }

        private void FinalizeButton_Click(object sender, RoutedEventArgs e)
        {
            CategoryLawyerRadio.IsChecked = true;
            SubTypeFinalRadio.IsChecked = true;

            ConfirmButton_Click(sender, e);
        }

        private void CancelButton_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }

        private bool TryParseLawyerFileName(string fileNameWithoutExt, out string date, out string typeTag, out string name, out string version)
        {
            date = typeTag = name = version = "";

            if (fileNameWithoutExt.Length < 10) return false;

            if (!Regex.IsMatch(fileNameWithoutExt.Substring(0, 8), @"^\d{8}$")) return false;

            var sep = fileNameWithoutExt[8];
            if (sep != '-' && sep != '_') return false;

            date = fileNameWithoutExt.Substring(0, 8);
            var rest = fileNameWithoutExt.Substring(9);

            if (!rest.StartsWith("【")) return false;
            var tagEnd = rest.IndexOf("】");
            if (tagEnd < 0) return false;

            typeTag = rest.Substring(0, tagEnd + 1);
            var tagContent = rest.Substring(1, tagEnd - 1);

            if (tagContent != "客户" && tagContent != "初稿" && tagContent != "终稿"
                && !Regex.IsMatch(tagContent, @"^修订V[\d.]+$"))
                return false;

            rest = rest.Substring(tagEnd + 1);

            if (rest.Length == 0) return false;
            if (rest[0] != '-' && rest[0] != '_') return false;
            rest = rest.Substring(1);

            var versionMatch = Regex.Match(rest, @"[-_]V[\d.]+$");
            if (versionMatch.Success)
            {
                version = versionMatch.Value.Substring(1);
                name = rest.Substring(0, rest.Length - versionMatch.Value.Length);
            }
            else
            {
                name = rest;
                version = "";
            }

            return !string.IsNullOrEmpty(name);
        }
    }
}
