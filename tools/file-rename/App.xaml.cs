using System.Windows;

namespace LegalFileRenamer
{
    public partial class App : Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            if (e.Args.Length > 0)
            {
                var filePath = e.Args[0];
                var mainWindow = new MainWindow(filePath);
                mainWindow.ShowDialog();
            }
            else
            {
                MessageBox.Show("请通过右键菜单启动此程序。", "提示", MessageBoxButton.OK, MessageBoxImage.Information);
            }

            Shutdown();
        }
    }
}
