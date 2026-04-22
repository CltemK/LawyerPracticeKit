package com.phoneguardian.ui.dashboard

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.github.mikephil.charting.components.XAxis
import com.github.mikephil.charting.data.Entry
import com.github.mikephil.charting.data.LineData
import com.github.mikephil.charting.data.LineDataSet
import com.phoneguardian.R
import com.phoneguardian.databinding.FragmentDashboardBinding
import com.phoneguardian.util.TimeUtils
import kotlinx.coroutines.launch

class DashboardFragment : Fragment() {

    private var _binding: FragmentDashboardBinding? = null
    private val binding get() = _binding!!

    private val viewModel: DashboardViewModel by viewModels()

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentDashboardBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupBatteryChart()
        observeUiState()
    }

    private fun observeUiState() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    updateScreenTime(state.todayScreenTime)
                    updateSleepStatus(state)
                    updateBattery(state)
                    updateTopApps(state.topApps)
                    updateBatteryChart(state)
                }
            }
        }
    }

    private fun updateScreenTime(durationMs: Long) {
        binding.tvScreenTime.text = TimeUtils.formatDuration(durationMs)
        binding.tvScreenTimeLabel.text = "今日亮屏时长"
    }

    private fun updateSleepStatus(state: DashboardUiState) {
        binding.tvSleepStatus.text = state.sleepStatus.message
        val sleepColor = if (state.sleepStatus.isGood) {
            resources.getColor(R.color.battery_good, null)
        } else {
            resources.getColor(R.color.sleep_warning, null)
        }
        binding.tvSleepStatus.setTextColor(sleepColor)
    }

    private fun updateBattery(state: DashboardUiState) {
        binding.tvBatteryLevel.text = "${state.currentBattery}%"

        val batteryColor = when {
            state.currentBattery > 50 -> R.color.battery_good
            state.currentBattery > 20 -> R.color.battery_medium
            else -> R.color.battery_low
        }
        binding.tvBatteryLevel.setTextColor(resources.getColor(batteryColor, null))

        binding.tvChargingStatus.text = if (state.isCharging) "充电中" else "未充电"
    }

    private fun updateTopApps(topApps: List<AppUsage>) {
        val appText = if (topApps.isEmpty()) {
            "暂无数据"
        } else {
            topApps.mapIndexed { index, app ->
                "${index + 1}. ${app.name} ${TimeUtils.formatDuration(app.duration)}"
            }.joinToString("\n")
        }
        binding.tvTopApps.text = appText
    }

    private fun setupBatteryChart() {
        binding.chartBattery.apply {
            description.isEnabled = false
            setTouchEnabled(false)
            legend.isEnabled = false
            setDrawGridBackground(false)

            xAxis.apply {
                position = XAxis.XAxisPosition.BOTTOM
                setDrawGridLines(false)
                granularity = 1f
            }

            axisLeft.apply {
                axisMinimum = 0f
                axisMaximum = 100f
                setDrawGridLines(true)
            }

            axisRight.isEnabled = false
        }
    }

    private fun updateBatteryChart(state: DashboardUiState) {
        if (state.batteryCurve.isEmpty()) return

        val entries = state.batteryCurve.mapIndexed { index, event ->
            Entry(index.toFloat(), event.level.toFloat())
        }

        val dataSet = LineDataSet(entries, "电量").apply {
            color = resources.getColor(R.color.primary, null)
            lineWidth = 2f
            setDrawCircles(false)
            setDrawValues(false)
            mode = LineDataSet.Mode.CUBIC_BEZIER
        }

        binding.chartBattery.data = LineData(dataSet)
        binding.chartBattery.invalidate()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
