import unittest
from unittest.mock import patch

from jobs_app_traffic_monitor.app_resolver import AppIdentity
from jobs_app_traffic_monitor.collectors.macos_nettop import MacOSNettopCollector, parse_nettop_row
from jobs_app_traffic_monitor.models import ProcessTraffic


class NettopParserTests(unittest.TestCase):
    def test_parse_process_row(self) -> None:
        line = "09:57:37.0,Google Chrome Helper.123,,,2048,1024,0,0,0,,,,"

        self.assertEqual(parse_nettop_row(line), ("Google Chrome Helper", 123, 2048, 1024))

    def test_ignores_header_and_invalid_rows(self) -> None:
        self.assertIsNone(parse_nettop_row("time,,interface,state,bytes_in,bytes_out"))
        self.assertIsNone(parse_nettop_row("09:57:37.0,missing-pid,,,2,1"))

    def test_calculates_deltas_and_rates(self) -> None:
        collector = MacOSNettopCollector()
        with (
            patch.object(
                collector._resolver,
                "resolve",
                return_value=AppIdentity("Example", None, "/tmp/Example", False),
            ),
            patch(
                "jobs_app_traffic_monitor.collectors.macos_nettop.time.monotonic",
                side_effect=(10.0, 12.0),
            ),
        ):
            collector._consume("Example", 99, 1000, 500)
            collector._consume("Example", 99, 1400, 700)

        item = collector._traffic[99]
        self.assertEqual(item.sample_bytes_in, 400)
        self.assertEqual(item.sample_bytes_out, 200)
        self.assertEqual(item.download_rate, 200)
        self.assertEqual(item.upload_rate, 100)

    def test_groups_helpers_from_the_same_app(self) -> None:
        processes = tuple(
            ProcessTraffic(
                pid=pid,
                process_name=name,
                app_name="Example App",
                app_path="/Applications/Example.app",
                reveal_path="/Applications/Example.app",
                is_system=False,
                bytes_in=bytes_in,
                bytes_out=bytes_out,
                sample_bytes_in=10,
                sample_bytes_out=5,
                download_rate=10,
                upload_rate=5,
                updated_at=1,
            )
            for pid, name, bytes_in, bytes_out in (
                (10, "Example", 100, 50),
                (11, "Example Helper", 200, 75),
            )
        )

        apps = MacOSNettopCollector._aggregate_apps(processes)

        self.assertEqual(len(apps), 1)
        self.assertEqual(apps[0].pids, (10, 11))
        self.assertEqual(apps[0].bytes_in, 300)
        self.assertEqual(apps[0].bytes_out, 125)
        self.assertFalse(apps[0].is_system)
        self.assertEqual(apps[0].reveal_path, "/Applications/Example.app")


if __name__ == "__main__":
    unittest.main()
